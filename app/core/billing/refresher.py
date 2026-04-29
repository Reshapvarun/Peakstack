import hashlib
import requests
import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple
from app.core.billing.models import HTTariffModel

class TariffRefreshManager:
    """
    Refined Non-invasive Tariff Refresh System.
    Uses a multi-signal approach to distinguish between general website
    updates and likely regulatory tariff changes.
    """
    def __init__(self, config_path: str = "config/state_tariffs.json", hash_path: str = "config/tariff_hashes.json"):
        self.config_path = config_path
        self.hash_path = hash_path
        self.state_data = self._load_state_tracking()

    def _load_state_tracking(self) -> Dict[str, Any]:
        if os.path.exists(self.hash_path):
            with open(self.hash_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_state_tracking(self):
        with open(self.hash_path, 'w') as f:
            json.dump(self.state_data, f, indent=2)

    def _extract_pdf_links(self, html_content: str) -> List[str]:
        """Extracts links that likely point to tariff PDFs."""
        # Look for .pdf links containing keywords like tariff, order, schedule, rates
        pattern = r'href=["\']([^"\']+\.pdf[^"\']*)["\']'
        links = re.findall(pattern, html_content, re.IGNORECASE)
        keywords = ['tariff', 'order', 'schedule', 'rate', 'bill', 'ht']
        return [l for l in links if any(k in l.lower() for k in keywords)]

    def check_for_update(self, state: str) -> Dict[str, Any]:
        """
        Multi-signal check to determine update confidence.
        Returns a confidence level: 'high', 'low', or 'none'.
        """
        with open(self.config_path, 'r') as f:
            config = json.load(f)

        if state not in config:
            return {"status": "error", "message": f"State {state} not found in config."}

        source_url = config[state].get('source_url')
        if not source_url:
            return {"status": "no_source", "message": "No source URL defined for this state."}

        try:
            response = requests.get(source_url, timeout=10)
            response.raise_for_status()
            content = response.content
            html_text = content.decode('utf-8', errors='ignore')

            # Signals
            current_hash = hashlib.sha256(content).hexdigest()
            last_modified = response.headers.get('Last-Modified', 'unknown')
            pdf_links = self._extract_pdf_links(html_text)

            stored = self.state_data.get(state, {})
            stored_hash = stored.get('content_hash')
            stored_lm = stored.get('last_modified')
            stored_pdfs = stored.get('pdf_links', [])

            # Update tracking data
            self.state_data[state] = {
                "content_hash": current_hash,
                "last_modified": last_modified,
                "pdf_links": pdf_links,
                "last_verified": datetime.now().strftime("%Y-%m-%d")
            }
            self._save_state_tracking()

            if not stored_hash:
                return {
                    "status": "initialized",
                    "confidence": "none",
                    "message": "Source tracked for the first time.",
                    "last_verified": self.state_data[state]['last_verified']
                }

            # Analysis
            hash_changed = current_hash != stored_hash
            lm_changed = (last_modified != 'unknown') and (last_modified != stored_lm)
            pdfs_changed = set(pdf_links) != set(stored_pdfs)

            if not hash_changed:
                return {
                    "status": "no_change",
                    "confidence": "none",
                    "message": "Tariff is up to date.",
                    "last_verified": self.state_data[state]['last_verified']
                }

            # High Confidence: Both content hash AND (Last-Modified or PDF links) changed
            if hash_changed and (lm_changed or pdfs_changed):
                return {
                    "status": "update_detected",
                    "confidence": "high",
                    "message": "Tariff update likely detected from official source.",
                    "source_url": source_url,
                    "last_verified": self.state_data[state]['last_verified']
                }

            # Low Confidence: Only the general content hash changed (UI update likely)
            return {
                "status": "update_detected",
                "confidence": "low",
                "message": "Possible website update detected (may not be tariff change).",
                "source_url": source_url,
                "last_verified": self.state_data[state]['last_verified']
            }

        except Exception as e:
            return {"status": "error", "message": f"Failed to check source: {str(e)}"}

    def update_tariff_manual(self, state: str, new_data: Dict[str, Any]):
        """Updates tariff config and resets the tracking hash."""
        with open(self.config_path, 'r') as f:
            config = json.load(f)

        from app.core.billing.models import HTTariffModel
        try:
            HTTariffModel(**new_data)
        except Exception as e:
            return {"status": "error", "message": f"Invalid tariff data structure: {str(e)}"}

        config[state] = new_data
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

        # Force a refresh to update the hash
        self.check_for_update(state)

        return {"status": "success", "message": f"Tariff for {state} updated successfully."}

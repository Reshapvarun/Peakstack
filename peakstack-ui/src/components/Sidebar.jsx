import { motion } from "framer-motion";

export default function Sidebar() {
  return (
    <motion.div
      initial={{ x: -200 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.4 }}
      className="sidebar"
    >
      <img src="/src/assets/logo.png" className="logo" />

      <h3>CONFIGURATION</h3>

      <button className="run-btn">🚀 Run Investment Analysis</button>
    </motion.div>
  );
}
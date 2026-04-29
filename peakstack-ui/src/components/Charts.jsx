import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  LineChart, Line, CartesianGrid
} from "recharts";

export default function Charts({ data }) {

  const barData = [
    { name: "Without BESS", value: data.without_bess },
    { name: "With BESS", value: data.with_bess }
  ];

  return (
    <div className="charts">

      <div className="chart-card">
        <h4>Cost Comparison</h4>
        <BarChart width={300} height={200} data={barData}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#22c55e" />
        </BarChart>
      </div>

      <div className="chart-card">
        <h4>Load Profile</h4>
        <LineChart width={300} height={200} data={data.load_profile}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#3b82f6" />
        </LineChart>
      </div>

    </div>
  );
}
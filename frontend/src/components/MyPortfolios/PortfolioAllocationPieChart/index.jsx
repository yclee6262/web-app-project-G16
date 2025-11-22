import { PieChart, Pie, Cell, Legend } from "recharts";

export default function PortfolioAllocationPieChart({ data }) {
  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#AF19FF"];
  const totalValue = data.reduce(
    (sum, asset) => sum + asset.quantity * asset.price,
    0
  );
  data = data.map((asset) => ({
    ...asset,
    allocation:
      (((asset.quantity * asset.price) / totalValue) * 100),
  }));
  return (
    <PieChart width={400} height={350}>
      <Pie
        data={data}
        cx="50%"
        cy="50%"
        outerRadius="50%"
        fill="#8884d8"
        paddingAngle={5}
        nameKey="ticker"
        dataKey="allocation"
        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
      >
        {data.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
        ))}
      </Pie>
      <Legend />
    </PieChart>
  );
}

import Dashboard from "../src/components/Dashboard";
import results from "../public/data/results.json";

export default function Page() {
  return <Dashboard data={results} />;
}

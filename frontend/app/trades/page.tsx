import { getTrades } from "@/lib/api/trades";
import { TradesView } from "./trades-view";

export default async function TradesPage() {
  const trades = await getTrades();
  return <TradesView trades={trades} />;
}

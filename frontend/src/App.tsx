import { Route, Routes } from "react-router-dom";
import HomePage from "@/modules/home/HomePage";
import CreationLayout from "@/modules/creation/CreationLayout";
import CareerPage from "@/modules/career/CareerPage";
import AppShell from "@/modules/hud/AppShell";

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/create/*" element={<CreationLayout />} />
        <Route path="/career" element={<CareerPage />} />
      </Routes>
    </AppShell>
  );
}

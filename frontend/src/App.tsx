import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ErrorBoundary from "./components/ErrorBoundary";
import Dashboard from "./pages/Dashboard";
import OpportunityList from "./pages/OpportunityList";
import OpportunityDetail from "./pages/OpportunityDetail";
import Settings from "./pages/Settings";
import AppStoreDashboard from "./pages/AppStoreDashboard";

function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="opportunities" element={<OpportunityList />} />
          <Route path="opportunities/:id" element={<OpportunityDetail />} />
          <Route path="app-store" element={<AppStoreDashboard />} />
          <Route path="app-store/:id" element={<OpportunityDetail />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}

export default App;

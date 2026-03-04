import { Navigate } from "react-router-dom";

// Root "/" is handled by App.tsx and maps directly to Overview.
// This file is kept as a safety redirect.
const Index = () => <Navigate to="/" replace />;

export default Index;

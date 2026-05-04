import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import IdentifyPage from "./pages/IdentifyPage";
import TurtleListPage from "./pages/TurtleListPage";
import TurtleProfilePage from "./pages/TurtleProfilePage";
import AddTurtlePage from "./pages/AddTurtlePage";

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/"              element={<IdentifyPage />} />
        <Route path="/turtles"       element={<TurtleListPage />} />
        <Route path="/turtles/new"   element={<AddTurtlePage />} />
        <Route path="/turtles/:id"   element={<TurtleProfilePage />} />
      </Routes>
    </>
  );
}

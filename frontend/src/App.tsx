import { BrowserRouter, Routes, Route } from "react-router-dom";

import MovieList from "./pages/MovieList";
import SingleMovie from "./pages/SingleMovie";
import SingleStar from "./pages/SingleStar";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MovieList />} />
        <Route path="/movies/:id" element={<SingleMovie />} />
        <Route path="/stars/:id" element={<SingleStar />} />
      </Routes>
    </BrowserRouter>
  );
}
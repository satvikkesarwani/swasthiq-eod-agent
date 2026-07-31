import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/space-mono/400.css";
import "./styles/reset.css";
import "./styles/tokens.css";
import "./styles/globals.css";
import "./styles/utilities.css";
import "./styles/motion.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";

import { router } from "./app/router";

const root = document.getElementById("root");

if (root === null) {
  throw new Error("Root element was not found.");
}

createRoot(root).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);

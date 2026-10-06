// React entry point

import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App.jsx";


// find react mount point
const rootElement = document.getElementById("root");


// stop if mount point missing
if (!rootElement) {
  throw new Error("TaxSaint root element not found.");
}


// create react root
const root = ReactDOM.createRoot(rootElement);


// mount application
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
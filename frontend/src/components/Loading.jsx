// TaxSaint loading component

import React from "react";


// reusable loading indicator
function Loading({
  message = "Loading..."
}) {

  // loading component layout
  return (
    <div
      id="taxsaint-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >

      {/* loading spinner */}
      <div
        id="loading-spinner"
        aria-hidden="true"
      />


      {/* loading message */}
      <span id="loading-message">
        {message}
      </span>

    </div>
  );
}


// export loading component
export default Loading;
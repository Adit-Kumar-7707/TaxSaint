// TaxSaint error message component

import React from "react";


// reusable error message
function ErrorMessage({
  message = "Something went wrong.",
  onRetry = null
}) {

  // handle retry action
  const handleRetry = () => {

    // run retry callback
    if (typeof onRetry === "function") {
      onRetry();
    }
  };


  // error message layout
  return (
    <div
      id="taxsaint-error"
      role="alert"
      aria-live="assertive"
    >

      {/* error heading */}
      <h3 id="error-title">
        Error
      </h3>


      {/* error description */}
      <p id="error-message">
        {message}
      </p>


      {/* retry action */}
      {typeof onRetry === "function" && (
        <button
          type="button"
          id="error-retry-button"
          onClick={handleRetry}
        >
          Try Again
        </button>
      )}

    </div>
  );
}


// export error component
export default ErrorMessage;
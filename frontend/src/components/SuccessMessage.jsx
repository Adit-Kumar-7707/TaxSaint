// TaxSaint success message component

import React from "react";


// reusable success message
function SuccessMessage({
  message = "Operation completed successfully.",
  onDismiss = null
}) {

  // handle dismiss action
  const handleDismiss = () => {

    // run dismiss callback
    if (typeof onDismiss === "function") {
      onDismiss();
    }
  };


  // success message layout
  return (
    <div
      id="taxsaint-success"
      role="status"
      aria-live="polite"
    >

      {/* success heading */}
      <h3 id="success-title">
        Success
      </h3>


      {/* success description */}
      <p id="success-message">
        {message}
      </p>


      {/* dismiss action */}
      {typeof onDismiss === "function" && (
        <button
          type="button"
          id="success-dismiss-button"
          onClick={handleDismiss}
        >
          Dismiss
        </button>
      )}

    </div>
  );
}


// export success component
export default SuccessMessage;
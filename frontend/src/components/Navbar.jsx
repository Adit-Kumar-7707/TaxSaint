// TaxSaint navigation bar

import React from "react";


// navigation bar component
function Navbar({
  title = "TaxSaint",
  userName = "",
  onProfileClick
}) {

  // handle profile action
  const handleProfileClick = () => {

    // run parent callback
    if (typeof onProfileClick === "function") {
      onProfileClick();
    }
  };


  // navigation bar layout
  return (
    <header id="taxsaint-navbar">

      {/* application branding */}
      <div id="navbar-brand">
        <h1>{title}</h1>
      </div>


      {/* application description */}
      <div id="navbar-page-info">
        <span>Tax & Financial Assistance</span>
      </div>


      {/* user controls */}
      <div id="navbar-user">

        {userName && (
          <span id="navbar-user-name">
            {userName}
          </span>
        )}

        <button
          type="button"
          id="navbar-profile-button"
          onClick={handleProfileClick}
        >
          Profile
        </button>

      </div>

    </header>
  );
}


// export navigation bar
export default Navbar;
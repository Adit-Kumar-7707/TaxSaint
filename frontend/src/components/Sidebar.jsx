// TaxSaint application sidebar

import React from "react";


// sidebar component
function Sidebar({
  currentPage = "dashboard",
  onPageChange
}) {

  // navigation items
  const navigationItems = [
    {
      id: "dashboard",
      label: "Dashboard"
    },
    {
      id: "profile",
      label: "Profile"
    },
    {
      id: "salaried",
      label: "Salaried Employee"
    },
    {
      id: "business",
      label: "Business Owner"
    }
  ];


  // handle navigation
  const handlePageChange = (page) => {

    // call parent navigation
    if (typeof onPageChange === "function") {
      onPageChange(page);
    }
  };


  // sidebar layout
  return (
    <aside id="taxsaint-sidebar">

      {/* sidebar branding */}
      <div id="sidebar-brand">
        <h2>TaxSaint</h2>
      </div>


      {/* main navigation */}
      <nav id="sidebar-navigation">

        {navigationItems.map((item) => (
          <button
            key={item.id}
            type="button"
            className={
              currentPage === item.id
                ? "sidebar-item active"
                : "sidebar-item"
            }
            onClick={() => handlePageChange(item.id)}
          >
            {item.label}
          </button>
        ))}

      </nav>

    </aside>
  );
}


// export sidebar
export default Sidebar;
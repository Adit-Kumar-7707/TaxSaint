// TaxSaint page container

import React from "react";


// reusable page container
function PageContainer({
  title = "",
  subtitle = "",
  children
}) {

  // check heading availability
  const hasHeader = Boolean(title || subtitle);


  // page container layout
  return (
    <main
      id="taxsaint-page-container"
      role="main"
    >

      {/* page heading */}
      {hasHeader && (
        <header id="page-header">

          {title && (
            <h1 id="page-title">
              {title}
            </h1>
          )}

          {subtitle && (
            <p id="page-subtitle">
              {subtitle}
            </p>
          )}

        </header>
      )}


      {/* page content */}
      <section id="page-content">
        {children}
      </section>

    </main>
  );
}


// export page container
export default PageContainer;
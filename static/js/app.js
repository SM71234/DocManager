document.addEventListener(
    "DOMContentLoaded",
    () => {

        const sidebar =
            document.querySelector(".sidebar");

        const toggle =
            document.getElementById(
                "menuToggle"
            );

        const overlay =
            document.getElementById(
                "sidebarOverlay"
            );

        if(toggle){

            toggle.addEventListener(
                "click",
                () => {

                    sidebar.classList.toggle(
                        "active"
                    );

                    overlay.classList.toggle(
                        "active"
                    );

                }
            );

            overlay.addEventListener(
                "click",
                () => {

                    sidebar.classList.remove(
                        "active"
                    );

                    overlay.classList.remove(
                        "active"
                    );

                }
            );

        }

    }
);
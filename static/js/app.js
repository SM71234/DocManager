/* ==========================================
   DocManager Global JavaScript System
   Command Palette, Dark Mode, Keyboard Shortcuts,
   Dynamic Greeting, Toast Notifications, FAB
   ========================================== */

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initGreetingAndClock();
    initCommandPalette();
    initKeyboardShortcuts();
    initFAB();
});

/* --- Dark Mode Theme Manager --- */
function initTheme() {
    const savedTheme = localStorage.getItem("docmanager_theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);

    const toggleBtn = document.getElementById("themeToggleBtn");
    if (toggleBtn) {
        toggleBtn.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme");
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("docmanager_theme", newTheme);
            updateThemeIcon(newTheme);
            showToast(`Switched to ${newTheme} mode`, "info");
        });
    }
}

function updateThemeIcon(theme) {
    const icon = document.getElementById("themeToggleIcon");
    if (icon) {
        icon.className = theme === "dark" ? "bi bi-sun-fill text-warning" : "bi bi-moon-stars-fill text-primary";
    }
}

/* --- Live Greeting & Real-time Clock --- */
function initGreetingAndClock() {
    const greetingEl = document.getElementById("dynamicGreeting");
    const clockEl = document.getElementById("liveClock");

    function update() {
        const now = new Date();
        const hrs = now.getHours();

        if (greetingEl) {
            if (hrs < 12) greetingEl.textContent = "Good Morning";
            else if (hrs < 17) greetingEl.textContent = "Good Afternoon";
            else greetingEl.textContent = "Good Evening";
        }

        if (clockEl) {
            clockEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + 
                                  " | " + now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
        }
    }

    update();
    setInterval(update, 1000);
}

/* --- Command Palette (Ctrl + K) --- */
function initCommandPalette() {
    const cmdBackdrop = document.getElementById("cmdBackdrop");
    const cmdInput = document.getElementById("cmdInput");
    const cmdResults = document.getElementById("cmdResults");
    const cmdTriggers = document.querySelectorAll(".trigger-cmd");

    if (!cmdBackdrop) return;

    function openCmd() {
        cmdBackdrop.style.display = "flex";
        cmdInput.value = "";
        cmdInput.focus();
        fetchCmdResults("");
    }

    function closeCmd() {
        cmdBackdrop.style.display = "none";
    }

    cmdTriggers.forEach(btn => btn.addEventListener("click", openCmd));

    cmdBackdrop.addEventListener("click", (e) => {
        if (e.target === cmdBackdrop) closeCmd();
    });

    let debounceTimer;
    cmdInput.addEventListener("input", (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            fetchCmdResults(e.target.value.trim());
        }, 150);
    });

    function fetchCmdResults(query) {
        fetch(`/api/global-search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                renderCmdResults(data);
            })
            .catch(err => console.error("Error fetching search results:", err));
    }

    function renderCmdResults(items) {
        if (!items || items.length === 0) {
            cmdResults.innerHTML = `<div class="p-4 text-center text-muted">No matching records or actions found.</div>`;
            return;
        }

        cmdResults.innerHTML = items.map((item, idx) => `
            <a href="${item.url}" class="cmd-item ${idx === 0 ? 'active' : ''}">
                <i class="bi ${item.icon || 'bi-link-45deg'} fs-5"></i>
                <div class="flex-grow-1">
                    <div class="fw-semibold">${item.title}</div>
                    ${item.subtitle ? `<small class="text-muted">${item.subtitle}</small>` : ''}
                </div>
                <span class="badge bg-light text-dark border">${item.category}</span>
            </a>
        `).join("");
    }

    // Keyboard navigation inside Command Palette
    cmdInput.addEventListener("keydown", (e) => {
        const activeItem = cmdResults.querySelector(".cmd-item.active");
        const items = Array.from(cmdResults.querySelectorAll(".cmd-item"));

        if (e.key === "Escape") {
            closeCmd();
        } else if (e.key === "ArrowDown") {
            e.preventDefault();
            if (activeItem && items.length > 0) {
                const nextIdx = (items.indexOf(activeItem) + 1) % items.length;
                activeItem.classList.remove("active");
                items[nextIdx].classList.add("active");
                items[nextIdx].scrollIntoView({ block: "nearest" });
            }
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            if (activeItem && items.length > 0) {
                const prevIdx = (items.indexOf(activeItem) - 1 + items.length) % items.length;
                activeItem.classList.remove("active");
                items[prevIdx].classList.add("active");
                items[prevIdx].scrollIntoView({ block: "nearest" });
            }
        } else if (e.key === "Enter") {
            e.preventDefault();
            if (activeItem) {
                window.location.href = activeItem.getAttribute("href");
            }
        }
    });
}

/* --- Global Keyboard Shortcuts --- */
function initKeyboardShortcuts() {
    document.addEventListener("keydown", (e) => {
        // Ignore inside inputs/textareas
        const activeTag = document.activeElement.tagName;
        const isEditing = activeTag === "INPUT" || activeTag === "TEXTAREA" || activeTag === "SELECT";

        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
            e.preventDefault();
            const cmdBackdrop = document.getElementById("cmdBackdrop");
            if (cmdBackdrop) {
                if (cmdBackdrop.style.display === "flex") {
                    cmdBackdrop.style.display = "none";
                } else {
                    document.querySelector(".trigger-cmd")?.click();
                }
            }
        } else if (!isEditing) {
            if (e.key.toLowerCase() === "n") {
                e.preventDefault();
                window.location.href = "/add-patient";
            } else if (e.key === "/") {
                e.preventDefault();
                document.querySelector(".trigger-cmd")?.click();
            }
        }
    });
}

/* --- Floating Action Button (FAB) --- */
function initFAB() {
    const fabMain = document.getElementById("fabMain");
    const fabContainer = document.getElementById("fabContainer");

    if (fabMain && fabContainer) {
        fabMain.addEventListener("click", () => {
            fabContainer.classList.toggle("active");
        });

        document.addEventListener("click", (e) => {
            if (!fabContainer.contains(e.target)) {
                fabContainer.classList.remove("active");
            }
        });
    }
}

/* --- Dynamic Toast Notification System --- */
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `alert alert-${type === "error" ? "danger" : type} alert-dismissible fade show shadow-lg border-0`;
    toast.style.minWidth = "280px";
    toast.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <i class="bi ${type === 'success' ? 'bi-check-circle-fill' : 'bi-info-circle-fill'} fs-5"></i>
            <div>${message}</div>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 200);
    }, 4000);
}
const BACKEND_URL = "https://smart-glasses-backend.onrender.com/api"; 

// Run immediately when any page loads to handle routing rules securely
document.addEventListener("DOMContentLoaded", () => {
    const currentPage = window.location.pathname;
    const isLoggedIn = sessionStorage.getItem("isLoggedIn");

    // Guard Wall: If a user tries to access home.html directly without logging in, kick them out to index.html
    if (currentPage.includes("home.html") && isLoggedIn !== "true") {
        alert("🔒 Unauthorized Access! Please log in first.");
        window.location.href = "index.html";
    }

    // If a user is logged in and stumbles back onto index.html, fast-track them to home
    if (currentPage.includes("index.html") && isLoggedIn === "true") {
        window.location.href = "home.html";
    }
});

// Toggle between Login and Register Forms
function toggleAuth(type) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabs = document.querySelectorAll('.tab-link');

    if (!loginForm || !registerForm) return;

    if (type === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        tabs[0].classList.add('active');
        tabs[1].classList.remove('active');
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        tabs[0].classList.remove('active');
        tabs[1].classList.add('active');
    }
}

/* ==========================================
   AUTHENTICATION STREAM
   ========================================== */

async function handleRegister(event) {
    event.preventDefault();
    const name = document.getElementById("registerName").value.trim();
    const email = document.getElementById("registerEmail").value.trim();
    const password = document.getElementById("registerPassword").value;

    try {
        const response = await fetch(`${BACKEND_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password })
        });
        
        const result = await response.json().catch(() => ({}));
        
        if (response.ok) {
            alert("🎉 Account created successfully! Please log in.");
            event.target.reset();
            toggleAuth('login');
            document.getElementById("loginEmail").value = email;
        } else {
            alert("❌ Registration Failed: " + (result.message || "Unknown server error."));
        }
    } catch (error) {
        console.error("Fetch Error:", error);
        alert("❌ Connection Fail: Could not reach the cloud server.");
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;

    try {
        const response = await fetch(`${BACKEND_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        
        const result = await response.json().catch(() => ({}));
        
        if (response.ok) {
            sessionStorage.setItem("isLoggedIn", "true");
            sessionStorage.setItem("userEmail", email);
            window.location.href = "home.html";
        } else {
            alert("❌ Login Failed: " + (result.message || "Invalid credentials."));
        }
    } catch (error) {
        console.error("Fetch Error:", error);
        alert("❌ Connection Fail: Cloud server timeout.");
    }
}

function handleLogout(event) {
    event.preventDefault();
    sessionStorage.clear();
    alert("👋 Logged out successfully.");
    window.location.href = "index.html";
}

/* ==========================================
   CHECKOUT & COMMERCE
   ========================================== */

function openCheckout() {
    document.getElementById('checkoutModal').style.display = 'block';
    calculateTotal(); 
}

function closeCheckout() {
    document.getElementById('checkoutModal').style.display = 'none';
}

function calculateTotal() {
    const basePrice = parseFloat(document.getElementById('basePrice').getAttribute('data-price'));
    const quantity = parseInt(document.getElementById('quantity').value) || 1;
    document.getElementById('totalAmount').value = `$${(basePrice * quantity).toFixed(2)}`;
}

async function handleCheckoutSubmit(event) {
    event.preventDefault();

    const payload = {
        email: sessionStorage.getItem("userEmail"),
        quantity: parseInt(document.getElementById('quantity').value),
        color: document.getElementById('color').value,
        location: document.getElementById('location').value,
        mpesa_code: document.getElementById('M-pesaCode').value.toUpperCase().trim(),
        total_amount: document.getElementById('totalAmount').value
    };

    try {
        const response = await fetch(`${BACKEND_URL}/purchase`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const result = await response.json().catch(() => ({}));
        
        if (response.ok) {
            alert("🛒 Order Sent Successfully! Check your inbox.");
            closeCheckout();
        } else {
            alert("❌ Server Error: " + (result.message || "Failed to process order."));
        }
    } catch (error) {
        alert("❌ Connection Error: Backend server currently unreachable.");
    }
}

function celebrate() {
    alert("🚀 Welcome to the Innovation Hub!");
}

function handleFormSubmit(event) {
    event.preventDefault();
    alert("✨ Message sent successfully!");
    document.getElementById("contactForm").reset();
}

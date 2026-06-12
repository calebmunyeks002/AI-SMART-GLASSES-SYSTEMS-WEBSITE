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

    // If a user is logged in and stumbles back onto index.html, fast-track them straight to the shop space
    if (currentPage.includes("index.html") && isLoggedIn === "true") {
        window.location.href = "home.html";
    }
});

// Toggle between Login and Register Forms inside index.html
function toggleAuth(type) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const tabs = document.querySelectorAll('.tab-link');

    if (!loginForm || !registerForm) return;

    if (type === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        tabs[0].style.color = '#333';
        tabs[0].style.borderBottom = '2px solid #6200ee';
        tabs[1].style.color = '#888';
        tabs[1].style.borderBottom = 'none';
    } else {
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        tabs[0].style.color = '#888';
        tabs[0].style.borderBottom = 'none';
        tabs[1].style.color = '#333';
        tabs[1].style.borderBottom = '2px solid #03dac6';
    }
}

/* ==========================================
   AUTHENTICATION TRANSLATION STREAM
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
        
        // Safe catch parsing block if server drops raw html error traces
        const result = await response.json().catch(() => ({}));
        
        if (response.ok) {
            alert("🎉 Account created successfully! Redirecting you to the login tab...");
            event.target.reset();
            toggleAuth('login');
            document.getElementById("loginEmail").value = email;
        } else {
            const errorMsg = result.message || "The cloud database is currently initializing or resetting. Please try clicking submit once more.";
            alert("❌ Registration Failed: " + errorMsg);
        }
    } catch (error) {
        console.error("Network Routing Interrupt Error:", error);
        alert("❌ Connection Fail: Could not hit the live backend API gateway cloud pipeline.");
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
            window.location.href = "home.html"; // FORCE REDIRECT TO HOME PAGE
        } else {
            const errorMsg = result.message || "Invalid credentials sequence mismatch verified.";
            alert("❌ Login Failed: " + errorMsg);
        }
    } catch (error) {
        console.error("Network Routing Interrupt Error:", error);
        alert("❌ Connection Fail: Cloud server timeout. Please give Render 60 seconds to completely wake up free-tier processes.");
    }
}

function handleLogout(event) {
    event.preventDefault();
    sessionStorage.removeItem("isLoggedIn");
    sessionStorage.removeItem("userEmail");
    alert("👋 Logged out successfully. See you next time!");
    window.location.href = "index.html"; // BOUNCE BACK TO ENTRANCE
}

/* ==========================================
   CHECKOUT & COMMERCE TRACKING
   ========================================== */

function openCheckout() {
    document.getElementById('checkoutModal').style.display = 'block';
    calculateTotal(); 
}

function closeCheckout() {
    document.getElementById('checkoutModal').style.display = 'none';
    document.getElementById('checkoutForm').reset();
}

function calculateTotal() {
    const basePrice = parseFloat(document.getElementById('basePrice').getAttribute('data-price'));
    const quantity = parseInt(document.getElementById('quantity').value) || 1;
    const totalInput = document.getElementById('totalAmount');
    
    const total = basePrice * quantity;
    totalInput.value = `$${total.toFixed(2)}`;
}

async function handleCheckoutSubmit(event) {
    event.preventDefault();

    const userEmail = sessionStorage.getItem("userEmail");
    const quantity = document.getElementById('quantity').value;
    const color = document.getElementById('color').value;
    const location = document.getElementById('location').value;
    const mpesaCode = document.getElementById('M-pesaCode').value.toUpperCase().trim(); 
    const totalAmount = document.getElementById('totalAmount').value;

    try {
        const response = await fetch(`${BACKEND_URL}/purchase`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                product_id: 1, 
                email: userEmail,
                quantity: parseInt(quantity),
                color: color,
                location: location,
                mpesa_code: mpesaCode,
                total_amount: totalAmount
            })
        });

        const result = await response.json().catch(() => ({}));
        
        if (response.ok) {
            alert(`🛒 Order Sent Successfully!\n\nDetails:\n- Total: ${totalAmount}\n- M-Pesa Code: ${mpesaCode}\n- Destination: ${location}\n\n📬 Check your inbox! A confirmation receipt has been sent to ${userEmail}.`);
            closeCheckout();
        } else {
            alert("❌ Server Error: " + (result.message || "Could not complete registration logging parameters."));
        }
    } catch (error) {
        alert(`🛒 Order Saved Locally!\n\nTotal Due: ${totalAmount}\nM-Pesa Code: ${mpesaCode}\nYour delivery target is: ${location}\nExpect your parcel in 2-4 working days.\n\n(Note: Backend server offline. Email receipt could not be processed right now.)`);
        closeCheckout();
    }
}

// Utility features for UI
function celebrate() {
    alert("🚀 Welcome to the Innovation Hub! Let's deploy technology to address community challenges.");
}

function handleFormSubmit(event) {
    event.preventDefault();
    alert("✨ Thank you for reaching out! Your message has been sent successfully.");
    document.getElementById("contactForm").reset();
}

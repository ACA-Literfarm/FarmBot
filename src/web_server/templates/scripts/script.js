document.addEventListener("DOMContentLoaded", () => {
  // Referencias a elementos del DOM
  const googleLoginBtn = document.getElementById("google-login")
  const emailLoginForm = document.getElementById("email-login-form")
  const togglePasswordBtn = document.getElementById("toggle-password")
  const passwordInput = document.getElementById("password")
  const successMessage = document.getElementById("success-message")
  const errorMessage = document.getElementById("error-message")

  // Función para mostrar/ocultar contraseña
  togglePasswordBtn.addEventListener("click", function () {
    const type = passwordInput.getAttribute("type") === "password" ? "text" : "password"
    passwordInput.setAttribute("type", type)
    this.classList.toggle("fa-eye")
    this.classList.toggle("fa-eye-slash")
  })

  // Función para manejar el inicio de sesión con Google
  googleLoginBtn.addEventListener("click", () => {
    console.log("Iniciando sesión con Google...")
    // Aquí iría la lógica de autenticación con Google usando el mismo API Token que LiteFarm
    // Por ahora, simulamos un inicio de sesión exitoso
    simulateLogin(true)
  })

  // Manejar el envío del formulario de correo electrónico y contraseña
  emailLoginForm.addEventListener("submit", (e) => {
    e.preventDefault()
    const email = document.getElementById("email").value.trim()
    const password = passwordInput.value

    if (email && password) {
      console.log("Iniciando sesión con email:", email)
      // Aquí iría la lógica de autenticación con email y contraseña
      // Por ahora, simulamos un inicio de sesión exitoso o fallido aleatoriamente
      const isSuccess = Math.random() > 0.5
      simulateLogin(isSuccess)
    } else {
      showError("Por favor, completa todos los campos")
    }
  })

  // Función para simular el proceso de inicio de sesión
  function simulateLogin(isSuccess) {
    // Ocultar ambos mensajes primero
    successMessage.classList.add("hidden")
    errorMessage.classList.add("hidden")

    // Simular un tiempo de carga
    setTimeout(() => {
      if (isSuccess) {
        showSuccess()
      } else {
        showError("Credenciales inválidas. Por favor, intenta nuevamente.")
      }
    }, 1000)
  }

  // Función para mostrar mensaje de éxito
  function showSuccess() {
    successMessage.classList.remove("hidden")
    errorMessage.classList.add("hidden")
  }

  // Función para mostrar mensaje de error
  function showError(message) {
    errorMessage.textContent = message
    errorMessage.classList.remove("hidden")
    successMessage.classList.add("hidden")
  }
})

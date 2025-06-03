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
    // Google OAuth is handled by the server-side redirect
  })

  // Manejar el envío del formulario de correo electrónico y contraseña
  emailLoginForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    const email = document.getElementById("email").value.trim()
    const password = passwordInput.value

    if (!email || !password) {
      showError("Por favor, completa todos los campos")
      return
    }

    // Hide any existing messages
    hideMessages()

    // Show loading state
    const submitBtn = emailLoginForm.querySelector('button[type="submit"]')
    const originalText = submitBtn.textContent
    submitBtn.disabled = true
    submitBtn.textContent = "Iniciando sesión..."

    try {
      // Get screen dimensions
      const screenWidth = window.screen.width
      const screenHeight = window.screen.height

      // Prepare form data
      const formData = new FormData()
      formData.append('email', email)
      formData.append('password', password)
      formData.append('screen_width', screenWidth.toString())
      formData.append('screen_height', screenHeight.toString())

      // Send login request
      const response = await fetch('/login', {
        method: 'POST',
        body: formData
      })

      const responseData = await response.json()

      if (response.ok && responseData.success) {
        // Successful login - redirect to success page
        if (responseData.redirect) {
          window.location.href = responseData.redirect
        } else {
          showSuccess("Inicio de sesión exitoso")
        }
      } else {
        // Handle error response
        const errorMessage = responseData.error || "Error al iniciar sesión"
        showError(errorMessage)
      }
    } catch (error) {
      console.error("Login error:", error)
      showError("Error de conexión. Por favor, intenta nuevamente.")
    } finally {
      // Reset button state
      submitBtn.disabled = false
      submitBtn.textContent = originalText
    }
  })

  // Función para ocultar todos los mensajes
  function hideMessages() {
    successMessage.classList.add("hidden")
    errorMessage.classList.add("hidden")
  }

  // Función para mostrar mensaje de éxito
  function showSuccess(message = "Inicio de sesión exitoso. Puedes regresar a Telegram.") {
    successMessage.querySelector('i').nextSibling.textContent = ` ${message}`
    successMessage.classList.remove("hidden")
    errorMessage.classList.add("hidden")
  }

  // Función para mostrar mensaje de error
  function showError(message) {
    errorMessage.querySelector('i').nextSibling.textContent = ` ${message}`
    errorMessage.classList.remove("hidden")
    successMessage.classList.add("hidden")
  }
})

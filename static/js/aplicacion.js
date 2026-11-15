const BASE_API = "/api";

let tokenAutenticacion = localStorage.getItem("jwt_token") || null;
let usuarioActual = null;
let idIngredienteEditando = null;

function mostrarAlerta(mensaje, tipo = "error") {
  const caja = document.getElementById("caja-alerta");
  if (!caja) return;
  caja.textContent = mensaje;
  caja.className = `alerta ${tipo === "exito" ? "alerta-exito" : "alerta-error"}`;
  caja.classList.remove("oculto");
  setTimeout(() => {
    caja.classList.add("oculto");
  }, 4500);
}

async function peticionApi(ruta, opciones = {}) {
  const cabeceras = opciones.headers ? { ...opciones.headers } : {};
  if (tokenAutenticacion) {
    cabeceras["Authorization"] = `Bearer ${tokenAutenticacion}`;
  }
  if (opciones.body && !(opciones.body instanceof FormData)) {
    cabeceras["Content-Type"] = "application/json";
  }

  const respuesta = await fetch(`${BASE_API}${ruta}`, {
    ...opciones,
    headers: cabeceras,
  });

  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    let mensajeError = datos.detail || "Ocurrió un error al procesar la solicitud.";
    if (Array.isArray(mensajeError)) {
      mensajeError = mensajeError.map((e) => e.msg).join(", ");
    }
    throw new Error(mensajeError);
  }
  return datos;
}

function cambiarPestanaAutenticacion(modo) {
  const pestanaLogin = document.getElementById("pestana-login");
  const pestanaRegistro = document.getElementById("pestana-registro");
  const grupoNombre = document.getElementById("grupo-nombre");
  const botonEnviar = document.getElementById("boton-enviar-auth");
  const formulario = document.getElementById("formulario-autenticacion");

  formulario.dataset.modo = modo;
  if (modo === "registro") {
    pestanaRegistro.classList.add("activa");
    pestanaLogin.classList.remove("activa");
    grupoNombre.classList.remove("oculto");
    botonEnviar.textContent = "Crear cuenta";
  } else {
    pestanaLogin.classList.add("activa");
    pestanaRegistro.classList.remove("activa");
    grupoNombre.classList.add("oculto");
    botonEnviar.textContent = "Iniciar sesión";
  }
}

async function enviarFormularioAutenticacion(evento) {
  evento.preventDefault();
  const formulario = evento.target;
  const modo = formulario.dataset.modo || "login";
  const nombre = document.getElementById("auth-nombre").value.trim();
  const email = document.getElementById("auth-correo").value.trim();
  const password = document.getElementById("auth-contrasena").value;

  try {
    let resultado;
    if (modo === "registro") {
      resultado = await peticionApi("/autenticacion/registro", {
        method: "POST",
        body: JSON.stringify({ nombre, email, password }),
      });
      mostrarAlerta("Cuenta creada con éxito. ¡Bienvenido!", "exito");
    } else {
      resultado = await peticionApi("/autenticacion/iniciar-sesion", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      mostrarAlerta("Sesión iniciada correctamente.", "exito");
    }

    tokenAutenticacion = resultado.access_token;
    usuarioActual = resultado.usuario;
    localStorage.setItem("jwt_token", tokenAutenticacion);
    formulario.reset();
    renderizarEstadoAplicacion();
  } catch (err) {
    mostrarAlerta(err.message, "error");
  }
}

function cerrarSesion() {
  tokenAutenticacion = null;
  usuarioActual = null;
  localStorage.removeItem("jwt_token");
  renderizarEstadoAplicacion();
}

async function verificarSesion() {
  if (!tokenAutenticacion) {
    renderizarEstadoAplicacion();
    return;
  }
  try {
    usuarioActual = await peticionApi("/autenticacion/perfil");
    renderizarEstadoAplicacion();
  } catch {
    cerrarSesion();
  }
}

function renderizarEstadoAplicacion() {
  const seccionAuth = document.getElementById("seccion-autenticacion");
  const seccionPanel = document.getElementById("seccion-panel");
  const navegacionUsuario = document.getElementById("navegacion-usuario");
  const etiquetaUsuario = document.getElementById("etiqueta-nombre-usuario");

  if (tokenAutenticacion && usuarioActual) {
    seccionAuth.classList.add("oculto");
    seccionPanel.classList.remove("oculto");
    navegacionUsuario.classList.remove("oculto");
    etiquetaUsuario.textContent = `${usuarioActual.nombre} (${usuarioActual.email})`;
    cargarIngredientes();
    cargarRecetas();
  } else {
    seccionAuth.classList.remove("oculto");
    seccionPanel.classList.add("oculto");
    navegacionUsuario.classList.add("oculto");
  }
}

async function cargarIngredientes() {
  const elementoLista = document.getElementById("lista-ingredientes");
  const insigniaContador = document.getElementById("contador-inventario");
  try {
    const elementos = await peticionApi("/ingredientes");
    insigniaContador.textContent = `${elementos.length} disponibles`;

    if (elementos.length === 0) {
      elementoLista.innerHTML = `
        <li class="estado-vacio">
          Tu inventario está vacío. Agrega los ingredientes que tienes en casa para generar recetas con IA.
        </li>`;
      return;
    }

    elementoLista.innerHTML = elementos
      .map(
        (item) => `
      <li class="item-ingrediente">
        <div class="info-ingrediente">
          <strong>${escaparHtml(item.nombre)}</strong>
          <span>${item.cantidad} ${escaparHtml(item.unidad)}</span>
        </div>
        <div class="acciones-ingrediente">
          <button class="boton boton-borde boton-pequeno" onclick="iniciarEdicionIngrediente(${item.id}, '${escaparComillas(item.nombre)}', ${item.cantidad}, '${escaparComillas(item.unidad)}')">
            Editar
          </button>
          <button class="boton boton-peligro boton-pequeno" onclick="eliminarIngrediente(${item.id})">
            Eliminar
          </button>
        </div>
      </li>`
      )
      .join("");
  } catch (err) {
    mostrarAlerta(err.message, "error");
  }
}

async function enviarFormularioIngrediente(evento) {
  evento.preventDefault();
  const nombre = document.getElementById("ing-nombre").value.trim();
  const cantidad = parseFloat(document.getElementById("ing-cantidad").value);
  const unidad = document.getElementById("ing-unidad").value.trim();

  try {
    if (idIngredienteEditando) {
      await peticionApi(`/ingredientes/${idIngredienteEditando}`, {
        method: "PUT",
        body: JSON.stringify({ nombre, cantidad, unidad }),
      });
      mostrarAlerta("Ingrediente actualizado en tu inventario.", "exito");
      cancelarEdicionIngrediente();
    } else {
      await peticionApi("/ingredientes", {
        method: "POST",
        body: JSON.stringify({ nombre, cantidad, unidad }),
      });
      mostrarAlerta("Ingrediente añadido al inventario.", "exito");
      document.getElementById("formulario-ingrediente").reset();
    }
    cargarIngredientes();
  } catch (err) {
    mostrarAlerta(err.message, "error");
  }
}

function iniciarEdicionIngrediente(id, nombre, cantidad, unidad) {
  idIngredienteEditando = id;
  document.getElementById("ing-nombre").value = nombre;
  document.getElementById("ing-cantidad").value = cantidad;
  document.getElementById("ing-unidad").value = unidad;
  document.getElementById("boton-guardar-ingrediente").textContent = "Guardar cambios";
  document.getElementById("boton-cancelar-ingrediente").classList.remove("oculto");
}

function cancelarEdicionIngrediente() {
  idIngredienteEditando = null;
  document.getElementById("formulario-ingrediente").reset();
  document.getElementById("boton-guardar-ingrediente").textContent = "+ Agregar al inventario";
  document.getElementById("boton-cancelar-ingrediente").classList.add("oculto");
}

async function eliminarIngrediente(id) {
  try {
    await peticionApi(`/ingredientes/${id}`, { method: "DELETE" });
    mostrarAlerta("Ingrediente eliminado.", "exito");
    cargarIngredientes();
  } catch (err) {
    mostrarAlerta(err.message, "error");
  }
}

async function generarRecetaIA(evento) {
  evento.preventDefault();
  const boton = document.getElementById("boton-generar");
  const tipoComida = document.getElementById("preferencia-receta").value.trim();

  boton.disabled = true;
  const textoOriginal = boton.textContent;
  boton.textContent = "Generando receta con IA...";

  try {
    const receta = await peticionApi("/recetas/generar", {
      method: "POST",
      body: JSON.stringify({ tipo_comida: tipoComida || null }),
    });
    mostrarAlerta(`¡Receta "${receta.nombre_del_plato}" generada y guardada!`, "exito");
    document.getElementById("preferencia-receta").value = "";
    cargarRecetas();
  } catch (err) {
    mostrarAlerta(err.message, "error");
  } finally {
    boton.disabled = false;
    boton.textContent = textoOriginal;
  }
}

async function cargarRecetas() {
  const contenedor = document.getElementById("contenedor-recetas");
  const soloGuardadas = document.getElementById("filtro-guardadas").checked;

  try {
    const recetas = await peticionApi(`/recetas?solo_guardadas=${soloGuardadas}`);
    if (recetas.length === 0) {
      contenedor.innerHTML = `
        <div class="estado-vacio">
          Aún no hay recetas en esta vista. ¡Agrega ingredientes a tu inventario y presiona "Generar Receta con IA"!
        </div>`;
      return;
    }

    contenedor.innerHTML = recetas
      .map((r) => {
        const estrellasHtml = [1, 2, 3, 4, 5]
          .map(
            (estrella) => `
          <button
            type="button"
            class="boton-estrella ${r.mi_calificacion && estrella <= r.mi_calificacion ? "activa" : ""}"
            title="Calificar con ${estrella} estrellas"
            onclick="calificarReceta(${r.id}, ${estrella})"
          >★</button>`
          )
          .join("");

        const textoPromedio = r.promedio_calificacion
          ? `★ ${r.promedio_calificacion} / 5`
          : "Sin calificar";

        return `
        <article class="tarjeta-receta">
          <div class="encabezado-receta">
            <div>
              <h3 class="titulo-receta">${escaparHtml(r.nombre_del_plato)}</h3>
              <div class="insignias-receta">
                <span class="insignia insignia-verde">⏱ ${escaparHtml(r.tiempo_estimado)}</span>
                <span class="insignia insignia-ambar">📊 Dificultad: ${escaparHtml(r.nivel_de_dificultad)}</span>
                <span class="insignia">${textoPromedio}</span>
              </div>
            </div>
            <div class="acciones-ingrediente">
              <button
                class="boton boton-borde boton-pequeno"
                onclick="alternarGuardarReceta(${r.id})"
              >
                ${r.guardada ? "★ Guardada" : "☆ Guardar"}
              </button>
              <button
                class="boton boton-peligro boton-pequeno"
                onclick="eliminarReceta(${r.id})"
              >
                Eliminar
              </button>
            </div>
          </div>

          <div class="titulo-seccion-receta">Ingredientes y cantidades</div>
          <div class="pastillas-ingredientes">
            ${r.ingredientes
              .map(
                (ing) =>
                  `<span class="pastilla-ingrediente"><strong>${escaparHtml(ing.nombre)}:</strong> ${escaparHtml(ing.cantidad)}</span>`
              )
              .join("")}
          </div>

          <div class="titulo-seccion-receta">Pasos de preparación</div>
          <ol class="pasos-receta">
            ${r.pasos_de_preparacion
              .map((paso) => `<li>${escaparHtml(paso)}</li>`)
              .join("")}
          </ol>

          <div class="caja-calificacion">
            <div>
              <strong style="font-size: 0.86rem;">Calificar receta (1 a 5 estrellas):</strong>
              <div class="grupo-estrellas">${estrellasHtml}</div>
            </div>
            <span style="font-size: 0.78rem; color: var(--texto-suave);">
              Generada el ${new Date(r.fecha_creacion).toLocaleDateString("es-CO")}
            </span>
          </div>
        </article>`;
      })
      .join("");
  } catch (err) {
    mostrarAlerta(err.message, "error");
  }
}

async function calificarReceta(idReceta, estrellas) {
  try {
    await peticionApi(`/recetas/${idReceta}/calificar`, {
      method: "POST",
      body: JSON.stringify({ puntuacion: estrellas }),
    });
    mostrarAlerta(`Has calificado la receta con ${estrellas} estrella(s).`, "exito");
    cargarRecetas();
  } catch (err) {
    mostrarAlerta(err.message, "error");
  }
}

async function alternarGuardarReceta(idReceta) {
  try {
    await peticionApi(`/recetas/${idReceta}/guardar`, { method: "PATCH" });
    cargarRecetas();
  } catch (err) {
    mostrarAlerta(err.message, "error");
  }
}

async function eliminarReceta(idReceta) {
  try {
    await peticionApi(`/recetas/${idReceta}`, { method: "DELETE" });
    mostrarAlerta("Receta eliminada del historial.", "exito");
    cargarRecetas();
  } catch (err) {
    mostrarAlerta(err.message, "error");
  }
}

function escaparHtml(cadena) {
  return String(cadena ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escaparComillas(cadena) {
  return String(cadena ?? "").replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

document.addEventListener("DOMContentLoaded", () => {
  verificarSesion();
});

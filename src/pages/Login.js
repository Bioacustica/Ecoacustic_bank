import React, { useState } from "react";
import Footer from "../components/Footer";
import Head from "../components/Head";
import LoadingModal from "../components/LoadingModal";
import Navbar from "../components/Navbar";
import { sendCredentialsData } from "../services";

require("typeface-poppins");
require("typeface-rubik");

function Login() {
  const [showModal, setShowModal] = useState(false);

  const [credentials, setCredentials] = useState({
    email: "",
    password: "",
  });

  const handleChange = (event) => {
    setCredentials({
      ...credentials,
      [event.target.name]: event.target.value,
    });
  };

  const sendCredentials = async (credentials) => {
    setShowModal(true);
    const response = await sendCredentialsData(credentials);
    console.log(response.status);
    console.log(response.data)

    if (response.status) {
      if (response.data ==="Logeado con exito") {
        window.location.href = "./admin";
        setShowModal(false);
      }else{
        setShowModal(false);
        alert("Por favor verifique los datos de entrada");
      }
    } else {
      alert("Por favor verifique los datos de entrada");
      setShowModal(false);
    }

    /*
    const fs = require("fs");
    const formData = new FormData();
    formData.append('email', credentials.email);
    formData.append('password', credentials.password);

    axios
      .post(baseUrl, formData)
      .then((response) => {
        console.log(response.data);
        return response.data;
      })
      .then((response) => {
        // Aca se crean las cookies

        localStorage.setItem("token", response.access);
        localStorage.setItem("username", response.username);
        localStorage.setItem("rol", response.roles);
        alert(`Bienvenido ${response.username}`);
        window.location.href = "/admin";
      })
      .catch((error) => {
        console.log(error);
        alert(`Por favor verifique sus datos`);
      });
   */
  };

  return (
    <div>
      <div className="flex justify-center items-center">
        <Head />
      </div>
      <div className="flex justify-center items-center">
        <Navbar />
      </div>
      {showModal && <LoadingModal />}
      <div className="flex justify-center">
        <div className="justify-center w-341.5 h-165.25 bg-green-450 mt-8">
          <div className="h-0.625 bg-blue-850 mx-auto mt-14 w-79 mb-3"></div>
          <div className="text-center">
            <h1 className=" font-poppins font-extrabold text-4.5xl text-blue-850 mb-3">
              Iniciar Sesión
            </h1>
          </div>
          <div className="h-0.625 bg-blue-850 mx-auto w-79 "></div>

          <div className="mt-14 mb-10 text-white text-center font-rubik font-normal text-xl">
            <h1>
              Ingrese su dirección de correo electrónico para acceder al sistema{" "}
            </h1>
          </div>

          <form>
            <div className="flex w-341.5 justify-center items-center">
              <form className=" pt-6 ">
                <div className=" mb-6 justify-items-center">
                  <h1 className="text-left text-white  font-poppins font-semibold text-3xl">
                    Email
                  </h1>
                  <input
                    name="email"
                    type="text"
                    required
                    onChange={handleChange}
                    valor="usuario"
                    placeholder="Ingrese usuario"
                    className="placeholder-blue-850 bg-white w-166.25 h-10.75 font-rubik font-light  border-2 border-white border-opacity-100 "
                  />
                </div>
                <div className="mt-9">
                  <h1 className="text-left text-white font-poppins font-semibold text-3xl">
                    Contraseña
                  </h1>
                  <input
                    name="password"
                    onChange={handleChange}
                    type="password"
                    valor="contraseña"
                    required
                    placeholder="Ingrese contraseña"
                    className="placeholder-blue-850 w-166.25 h-10.75 mb-4 font-rubik font-light bg-white border-2 border-white border-opacity-100 "
                  />
                </div>
                <div className="flex justify-end w-166.25 mb-10 ">
                  <a
                    className=" text-white text-right
                    font-rubik font-normal text-xl
          hover:text-whithe border-b-2 border-green-450
          hover:border-b-2 hover:border-white"
                    href="/recoverpassword"
                  >
                    ¿Olvidaste tu contraseña?{" "}
                  </a>
                </div>
                <div className="flex justify-center w-166.25">
                  <button
                    className="w-76.25 h-13.5 bg-blue-850"
                    type="button"
                    onClick={() => sendCredentials(credentials)}
                  >
                    <h1 className="text-white font-poppins font-semibold text-4xl">
                      Ingresar
                    </h1>
                  </button>
                </div>
              </form>
            </div>
          </form>
        </div>
      </div>
      <div className="flex justify-center items-center mt-7.25">
        <Footer />
      </div>
    </div>
  );
}

export default Login;

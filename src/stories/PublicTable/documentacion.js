// CustomDocumentationComponent.js|jsx

import React from 'react';

export function CustomDocumentationComponent() {
 


  return (
    
    <div >
      <div className='flex items-center font-extrabold text-3xl justify-center text-blue-500'>
      <h1 >Tabla del filtro publico</h1>
      </div>
      <br/>
      <code>
        Autor: Alejandro Piedrahita Carvajal
      </code>
      <br/>
      <hr/>
      <br/>
      <h3 className='font-bold'>Descripcion</h3>
      <div className='flex items-center justify-start'>
      <p>
        Este componente hace referencia a la tabla de audios mostrada en el filtro publico en la pestaña de inicio de la aplicacion
      </p>
      </div>
      
      <br/>
      <h3 className='font-bold'>Funciones</h3>
      <p>
       No cuenta con ninguna funcion
      </p>
      <br/>
      <h3 className='font-bold'>Variables</h3>
      <p>
       No cuenta con ninguna variable de entrada o salida
      </p>
      <br/>
      <h3 className='font-bold'>Codigo</h3>
      <br/>

      
      <pre  className='border-2'>{
        <code className='w-139 h- justify-center'>{
        `
        <div className="flex">
        <div className="  border overflow-x-auto">
          <table className=" border border-collapse">
            <thead>
              <tr className="">
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Id
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Nombre
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Fecha
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Hábitat
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Departamento
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Municipio
                </td>
                <td className="border-2 font-rubik border-blue-850 text-base h-12.75 
                px-4 text-center">
                  Ciudad
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Elevación
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75
                 px-4 text-center">
                  Evento
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Formato
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75
                 px-4 text-center">
                  Tipo de micrófono
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Método de etiquetado
                </td>

                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Tipo de grabadora
                </td>
                <td className="border-2 font-rubik border-blue-850  text-base h-12.75 
                px-4 text-center">
                  Software de etiquetado
                </td>
                <td className="border-2 font-rubik border-blue-850 text-base h-12.75 
                px-4 text-center">
                  Tipo de carcasa
                </td>
              </tr>
            </thead>
  
            <tbody>
              {columns.map((rowscounter) => (
                <tr className="">
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75 
                  px-4 text-center">
                    Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75 
                  px-4 text-center">
                  Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75 
                  px-4 text-center">
                  Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75
                   px-4 text-center">
                  Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75 
                  px-4 text-center">
                  Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75 
                  px-4 text-center">
                  Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75
                   px-4 text-center">
                  Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75
                   px-4 text-center">
                  Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75 
                  px-4 text-center">
                    Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75
                   px-4 text-center">
                    Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75
                   px-4 text-center">
                    Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75
                   px-4 text-center">
                    Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75
                   px-4 text-center">
                    Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75 
                  px-4 text-center">
                    Dato_Audio{rowscounter}
                  </td>
                  <td className="border-2 font-rubik border-blue-850 font-light text-base h-12.75 
                  px-4 text-center">
                    Dato_Audio{rowscounter}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
  
        <div className="ml-8">
          <table>
            <thead>
              <tr className="">
                <td className=" font-rubik font-semibold text-base h-14 px-4 text-center"></td>
              </tr>
            </thead>
            <tbody>
              {columns.map((rowscounter) => (
                <tr>
                  <td className="font-rubik font-light text-base h-12.75 ml-4">
                    <button 
                    onClick={openModal}
                    className=" bg-yellow-400 font-semibold text-xl text-white  w-31.25">
                      Más
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {showModal && <MoreInformationModal className="z-50" close={closeModal}/>}
        </div>
      </div>
    `}
</code>

}</pre>
    </div>
  );
  
}


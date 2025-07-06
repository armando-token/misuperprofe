import React from 'react';
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

function App() {
  const [copilotKitHeaders, setCopilotKitHeaders] = React.useState<Record<string, string>>({});
  const [tokenProcessed, setTokenProcessed] = React.useState(false);

  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');
    console.log("Token extraído de la URL:", token);
    if (token) {
      const newHeaders = { 'Authorization': `Bearer ${token}` };
      console.log("Cabeceras para CopilotKit:", newHeaders);
      setCopilotKitHeaders(newHeaders);
    } else {
      console.log("No se encontró token en la URL");
    }
    setTokenProcessed(true);
  }, []);

  if (!tokenProcessed) {
    return <div>Cargando y configurando asistente...</div>;
  }

  return (
    <CopilotKit 
      runtimeUrl="http://18.214.59.62:4000/copilotkit" 
      headers={copilotKitHeaders.Authorization ? copilotKitHeaders : {}}
    >
      <CopilotPopup
        instructions="Ayúdame a interactuar con la plataforma MiSuperProfe."
        defaultOpen={true}
        labels={{
          title: "Asistente Virtual MiSuperProfe",
          initial: "Hola, ¿cómo puedo ayudarte hoy con tus cursos o estudios?",
        }}
      />
    </CopilotKit>
  );
}

export default App; 
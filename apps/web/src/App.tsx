import { useEffect, useState } from 'react'
import { getHealth, type HealthResponse } from './lib/api'
import { requestFormReset } from 'react-dom';

type RequestState = 
  | {status: "loading"}
  | {status: "success"; data: HealthResponse}
  | {status: "error"; message: string};

function App(){
  const [requestState, setRequestState] = useState<RequestState>({
    status: "loading",
  });

  useEffect(() => {
    async function checkApiHealth() {
      try{
        const data = await getHealth();
        setRequestState({status: "success", data});
      } catch (error){
        const message =
          error instanceof Error ? error.message : "Unknown error occurred";

        setRequestState({ status: "error", message });
      }
    }

    void checkApiHealth();
  }, [])

  return(
  <main className="app-shell">
    <section className="hero">
      <p className="eyebrow">Shipyard</p>
      <h1>Engineering work, releases, and operational clarity.</h1>
      <p className="description"> Phase 0 is complete when this frontend can successfully communicate with the Flask API.</p>

      <section className='status-card' aria-live='polite'>
        <h2>API Health</h2>

        {requestState.status === "loading" && ( 
          <p className='status loading'>
            Checking API connection...
          </p>
        )}

        {requestState.status === "success" && (
          <p className="status success">
            Connected to {requestState.data.serivce}. Status:{" "}{requestState.data.status}.
          </p>
        )}

        {requestState.status === "error" && (
          <p className="status error">
            API connection failed: {requestState.message}
          </p>
        )}
      </section>
    </section>
  </main>
  );
}

export default App;

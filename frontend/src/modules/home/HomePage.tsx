import { Link } from "react-router-dom";
import { useCareerStore } from "@/store/careerStore";

export default function HomePage() {
  const session = useCareerStore((state) => state.session);

  return (
    <div className="grid gap-8 lg:grid-cols-[1.4fr_1fr]">
      <section className="panel p-8 space-y-6">
        <div>
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Modo carrera
          </p>
          <h1 className="heading mt-2 text-5xl leading-none">
            De pibe del barrio
            <br />
            <span className="text-barrio-accent">a leyenda mundial.</span>
          </h1>
        </div>
        <p className="max-w-xl text-barrio-muted">
          Elegí de dónde venís, tu posición, tu número y armá tu propia
          historia. Cada decisión tiene peso — el club, la presión, la vida
          fuera de la cancha. Nada es al azar: lo que hacés hoy define
          quién sos mañana.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link to="/create" className="btn btn-primary">
            {session ? "Nueva carrera" : "Empezar carrera"}
          </Link>
          {session && (
            <Link to="/career" className="btn btn-gold">
              Continuar como {session.player.firstName}
            </Link>
          )}
        </div>
      </section>

      <section className="panel p-6 space-y-5">
        <h2 className="heading text-xl text-barrio-gold">¿Por qué ELBARRIO?</h2>
        <ul className="space-y-3 text-sm text-barrio-muted">
          <FeatureItem
            title="Decisiones con peso"
            body="Cada elección modifica tu estado, tu presión, tu felicidad. Nada es random."
          />
          <FeatureItem
            title="Vida real"
            body="Bodas, hijos inesperados, fiestas, ofertas tentadoras. Situaciones que exigen análisis."
          />
          <FeatureItem
            title="Consecuencias encadenadas"
            body="Una mala noche puede costar el clásico, y el clásico puede costar tu lugar en la selección."
          />
          <FeatureItem
            title="Dos carreras en una"
            body="Terminá como jugador y seguí como DT. La leyenda continúa."
          />
        </ul>
      </section>
    </div>
  );
}

function FeatureItem({ title, body }: { title: string; body: string }) {
  return (
    <li className="border-l-2 border-barrio-accent/40 pl-3">
      <p className="text-barrio-text font-semibold">{title}</p>
      <p>{body}</p>
    </li>
  );
}

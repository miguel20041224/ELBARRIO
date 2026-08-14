import { Link } from "react-router-dom";
import { useCareerStore } from "@/store/careerStore";

const gameplayPillars = [
  {
    title: "Carrera partido a partido",
    body: "Creás tu jugador, elegís liga y equipo, y avanzás con convocatorias, minutos esperados y mensajes del DT.",
  },
  {
    title: "Fútbol con contexto",
    body: "Cada fecha puede ser liga, copa o torneo continental, con sede, fase, tabla, trofeos y clásicos que pesan más.",
  },
  {
    title: "Mercado con contratos",
    body: "Los años de contrato importan: renovaciones, cláusulas, agencia libre, préstamos por pocos minutos y ofertas de élite.",
  },
  {
    title: "Historia viva",
    body: "Eventos, cadenas de consecuencias, ruletas de temporada, premios y títulos cambian cómo se cuenta tu carrera.",
  },
];

export default function HomePage() {
  const session = useCareerStore((state) => state.session);

  return (
    <div className="grid gap-8 lg:grid-cols-[1.35fr_1fr]">
      <section className="panel p-8 space-y-6">
        <div>
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Simulador de carrera futbolera
          </p>
          <h1 className="heading mt-2 text-5xl leading-none">
            Tu carrera se gana
            <br />
            <span className="text-barrio-accent">partido a partido.</span>
          </h1>
        </div>
        <p className="max-w-2xl text-barrio-muted">
          ELBARRIO ya se puede jugar como una carrera completa: creás tu
          jugador, elegís liga y equipo, peleás la convocatoria, jugás fechas
          con contexto real de competición y negociás tu futuro según contrato,
          rendimiento y reputación.
        </p>
        <div className="grid gap-3 text-sm text-barrio-muted sm:grid-cols-3">
          <StatCard label="Antes del partido" value="Rol probable" />
          <StatCard label="Temporada" value="Tabla y trofeos" />
          <StatCard label="Mercado" value="Contratos reales" />
        </div>
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
        <div>
          <p className="text-xs uppercase tracking-widest text-barrio-muted">
            Qué está vivo hoy
          </p>
          <h2 className="heading mt-1 text-xl text-barrio-gold">
            Pilares jugables
          </h2>
        </div>
        <ul className="space-y-3 text-sm text-barrio-muted">
          {gameplayPillars.map((pillar) => (
            <FeatureItem key={pillar.title} {...pillar} />
          ))}
        </ul>
      </section>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
      <p className="text-[0.65rem] uppercase tracking-widest text-barrio-muted">
        {label}
      </p>
      <p className="mt-1 font-semibold text-barrio-text">{value}</p>
    </div>
  );
}

function FeatureItem({ title, body }: { title: string; body: string }) {
  return (
    <li className="border-l-2 border-barrio-accent/40 pl-3">
      <p className="font-semibold text-barrio-text">{title}</p>
      <p>{body}</p>
    </li>
  );
}

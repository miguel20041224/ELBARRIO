import { useCreationStore } from "@/store/creationStore";
import { useCareerStore } from "@/store/careerStore";
import { COUNTRIES } from "@/data/countries";
import { LEAGUES } from "@/data/leagues";
import { POSITIONS } from "@/data/positions";

export default function ReviewStep() {
  const draft = useCreationStore((state) => state.draft);
  const loading = useCareerStore((state) => state.loading);
  const error = useCareerStore((state) => state.error);

  const country = COUNTRIES.find((c) => c.code === draft.birthCountry);
  const league = LEAGUES.find((l) => l.id === draft.startingLeague);
  const position = POSITIONS.find((p) => p.code === draft.position);

  return (
    <div className="space-y-6">
      <header>
        <h2 className="heading text-2xl">Confirmá tu carrera</h2>
        <p className="text-sm text-barrio-muted">
          Antes de arrancar, revisá los datos. Después de esto, cada temporada
          construye tu historia — no hay reset fácil.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <ReviewCard label="Nombre">
          {draft.firstName} {draft.lastName}
          {draft.nickname && (
            <span className="text-barrio-muted"> — "{draft.nickname}"</span>
          )}
        </ReviewCard>
        <ReviewCard label="Origen">
          {country ? `${country.flag} ${country.name}` : "—"}
        </ReviewCard>
        <ReviewCard label="Posición">
          {position ? `${position.code} · ${position.name}` : "—"}
        </ReviewCard>
        <ReviewCard label="Camiseta">
          #{draft.shirtNumber} · Pie {draft.preferredFoot}
        </ReviewCard>
        <ReviewCard label="Liga inicial">{league?.name ?? "—"}</ReviewCard>
        <ReviewCard label="Datos físicos">
          {draft.age} años · {draft.height} cm · {draft.weight} kg
        </ReviewCard>
      </div>

      {error && (
        <div className="rounded border border-barrio-danger/50 bg-barrio-danger/10 px-4 py-2 text-sm text-barrio-danger">
          {error}
        </div>
      )}
      {loading && (
        <p className="text-sm text-barrio-muted">Creando carrera...</p>
      )}
    </div>
  );
}

function ReviewCard({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded border border-barrio-border bg-barrio-bg/40 p-3">
      <p className="text-xs uppercase tracking-widest text-barrio-muted">
        {label}
      </p>
      <p className="mt-1 text-sm">{children}</p>
    </div>
  );
}

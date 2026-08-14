import { useCreationStore } from "@/store/creationStore";

export default function IdentityStep() {
  const draft = useCreationStore((state) => state.draft);
  const update = useCreationStore((state) => state.update);

  return (
    <div className="space-y-6">
      <header>
        <h2 className="heading text-2xl">Tu identidad</h2>
        <p className="text-sm text-barrio-muted">
          ¿Cómo te vas a llamar en el fútbol? El apodo lo eligen los hinchas —
          pero podés proponer uno.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Nombre">
          <input
            className="input"
            value={draft.firstName}
            onChange={(e) => update({ firstName: e.target.value })}
            placeholder="Ej: Diego"
            maxLength={30}
          />
        </Field>
        <Field label="Apellido">
          <input
            className="input"
            value={draft.lastName}
            onChange={(e) => update({ lastName: e.target.value })}
            placeholder="Ej: Rodríguez"
            maxLength={30}
          />
        </Field>
        <Field label="Apodo (opcional)">
          <input
            className="input"
            value={draft.nickname}
            onChange={(e) => update({ nickname: e.target.value })}
            placeholder="Ej: El Pibe"
            maxLength={20}
          />
        </Field>
        <Field label="Edad">
          <input
            type="number"
            min={16}
            max={22}
            className="input"
            value={draft.age}
            onChange={(e) => update({ age: Number(e.target.value) })}
          />
          <p className="text-xs text-barrio-muted mt-1">
            Empezás joven (16-22). Cuanto más chico, más tiempo tenés para
            crecer.
          </p>
        </Field>
        <Field label="Altura (cm)">
          <input
            type="number"
            min={155}
            max={205}
            className="input"
            value={draft.height}
            onChange={(e) => update({ height: Number(e.target.value) })}
          />
        </Field>
        <Field label="Peso (kg)">
          <input
            type="number"
            min={55}
            max={110}
            className="input"
            value={draft.weight}
            onChange={(e) => update({ weight: Number(e.target.value) })}
          />
        </Field>
      </div>

      <style>{`
        .input {
          width: 100%;
          background: rgba(31, 42, 58, 0.5);
          border: 1px solid #1f2a3a;
          border-radius: 0.375rem;
          padding: 0.5rem 0.75rem;
          color: #e2e8f0;
          transition: border-color 0.15s;
        }
        .input:focus {
          outline: none;
          border-color: #22c55e;
        }
      `}</style>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs uppercase tracking-widest text-barrio-muted">
        {label}
      </span>
      {children}
    </label>
  );
}

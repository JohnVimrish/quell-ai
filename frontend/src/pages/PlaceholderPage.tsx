type PlaceholderPageProps = {
  title: string;
};

export default function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <div className="section-padding">
      <div className="glass-panel" style={{ padding: "48px" }}>
        <h1 style={{ marginTop: 0 }}>{title}</h1>
        <p>
          This view will be implemented when backend data contracts are ready for the React
          frontend. For now it acts as a placeholder so routing and manifest integration can be
          validated end-to-end.
        </p>
      </div>
    </div>
  );
}




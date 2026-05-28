'use client';

function TweakButton({
  label,
  onClick,
  secondary = false,
}: {
  label: string;
  onClick: () => void;
  secondary?: boolean;
}) {
  return (
    <button type="button" className={secondary ? 'twk-btn secondary' : 'twk-btn'} onClick={onClick}>
      {label}
    </button>
  );
}
export default TweakButton;
export { TweakButton };

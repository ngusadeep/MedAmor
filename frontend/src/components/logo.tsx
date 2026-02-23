import { Link } from '@tanstack/react-router'

export const Logo = () => (
  <Link
    to="/"
    className="flex shrink-0 items-center"
    aria-label="MedArmor home"
  >
    <img
      src="/images/medarmor-logo.jpg"
      alt="MedArmor — Shielding Health"
      className="h-10 w-auto object-contain rounded-sm"
    />
  </Link>
)

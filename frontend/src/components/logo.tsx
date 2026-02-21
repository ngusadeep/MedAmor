import { Link } from '@tanstack/react-router'
import { Logo as LogoIcon } from '@/assets/logo'

export const Logo = () => (
  <Link
    to="/"
    className="flex shrink-0 items-center gap-2"
    aria-label="MedArmor home"
  >
    <LogoIcon className="size-7" />
    <span className="font-semibold text-lg">MedArmor</span>
  </Link>
)

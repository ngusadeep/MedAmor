import {
  ClipboardList,
  FileText,
  HelpCircle,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  UserCog,
  Wrench,
  Palette,
  Bell,
  Monitor,
  Users,
} from 'lucide-react'
import { type SidebarData } from '../types'

export const sidebarData: SidebarData = {
  user: {
    name: 'MedArmor User',
    email: '',
    avatar: '',
  },
  teams: [
    {
      name: 'MedArmor',
      logo: ShieldCheck,
      plan: 'Medical Audit',
    },
  ],
  navGroups: [
    {
      title: 'Main',
      items: [
        {
          title: 'Dashboard',
          url: '/',
          icon: LayoutDashboard,
        },
        {
          title: 'Patients',
          url: '/patients',
          icon: Users,
        },
        {
          title: 'Audit Jobs',
          url: '/audits/jobs',
          icon: ClipboardList,
        },
        {
          title: 'Audit Reports',
          url: '/audits/reports',
          icon: FileText,
        },
      ],
    },
    {
      title: 'Other',
      items: [
        {
          title: 'Settings',
          icon: Settings,
          items: [
            {
              title: 'Profile',
              url: '/settings',
              icon: UserCog,
            },
            {
              title: 'Account',
              url: '/settings/account',
              icon: Wrench,
            },
            {
              title: 'Appearance',
              url: '/settings/appearance',
              icon: Palette,
            },
            {
              title: 'Notifications',
              url: '/settings/notifications',
              icon: Bell,
            },
            {
              title: 'Display',
              url: '/settings/display',
              icon: Monitor,
            },
          ],
        },
        {
          title: 'Help Center',
          url: '/help-center',
          icon: HelpCircle,
        },
      ],
    },
  ],
}

export const REF_CATEGORIES = [
  { slug: 'sector', label: 'Sector' },
  { slug: 'sub_sector', label: 'Sub-Sector' },
  { slug: 'transaction_type', label: 'Transaction Type' },
  { slug: 'tier', label: 'Tier' },
  { slug: 'contact_type', label: 'Contact Type' },
  { slug: 'company_type', label: 'Company Type' },
  { slug: 'company_sub_type', label: 'Company Sub-Type' },
  { slug: 'deal_source_type', label: 'Deal Source Type' },
  { slug: 'passed_dead_reason', label: 'Passed/Dead Reason' },
  { slug: 'investor_type', label: 'Investor Type' },
];

export function getCategoryLabel(slug) {
  const found = REF_CATEGORIES.find((c) => c.slug === slug);
  return found ? found.label : slug;
}

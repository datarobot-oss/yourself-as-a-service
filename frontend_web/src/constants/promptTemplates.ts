export interface PromptTemplate {
  label: string;
  content: string;
}

export const PROMPT_TEMPLATES: PromptTemplate[] = [
  {
    label: 'Full Blog Post',
    content:
      'Draft a full Markdown (not just Slack markdown) blog post. Here are the key points:\n\n',
  },
  {
    label: 'New Memory',
    content: 'Store this:\n',
  },
];

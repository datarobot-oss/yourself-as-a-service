import { LayoutTemplate } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { PROMPT_TEMPLATES } from '@/constants/promptTemplates';

interface PromptTemplateSelectorProps {
  onSelectTemplate: (value: string) => void;
  disabled?: boolean;
}

export function PromptTemplateSelector({
  onSelectTemplate,
  disabled,
}: PromptTemplateSelectorProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="default"
          size="icon"
          disabled={disabled}
          title="Insert template"
          className="absolute top-2 left-2 z-10"
        >
          <LayoutTemplate />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" side="top">
        {PROMPT_TEMPLATES.map(({ label, content }) => (
          <DropdownMenuItem key={label} onSelect={() => onSelectTemplate(content)}>
            {label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

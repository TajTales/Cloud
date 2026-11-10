/** Narrow web integration surface; original upstream JavaScript retains its license headers. */
export class DisplayGenerator {
  constructor(contentManager: null, hotkeyHelpController: null);
  prepare(templatesHtml: string): Promise<void>;
  createTermEntry(entry: object, dictionaries: object[]): HTMLElement;
}

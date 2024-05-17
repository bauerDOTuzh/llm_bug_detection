// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
// -x-
import { IWidgetTracker } from '@jupyterlab/apputils';
import { ActivityMonitor, PathExt } from '@jupyterlab/coreutils';
import { IDocumentWidget } from '@jupyterlab/docregistry';
import { Widget } from '@lumino/widgets';
import { TableOfContentsModel } from './model';
import { TableOfContents } from './tokens';

/**
 * Timeout for throttling ToC rendering following model changes.
 *
 * @private
 */
const RENDER_TIMEOUT = 1000;
// -x-
/**
 * Abstract table of contents model factory for IDocumentWidget.
 */
export abstract class TableOfContentsFactory<
  W extends IDocumentWidget,
  H extends TableOfContents.IHeading = TableOfContents.IHeading
> implements TableOfContents.IFactory<W, H>
{
  /**
   * Constructor
   *
   * @param tracker Widget tracker
   */
  constructor(protected tracker: IWidgetTracker<W>) {}

  /**
   * Whether the factory can handle the widget or not.
   *
   * @param widget - widget
   * @returns boolean indicating a ToC can be generated
   */
  isApplicable(widget: Widget): boolean {
    if (!this.tracker.has(widget)) {
      return false;
    }

    return true;
  }

  /**
   * Create a new table of contents model for the widget
   *
   * @param widget - widget
   * @param configuration - Table of contents configuration
   * @returns The table of contents model
   */
  createNew(
    widget: W,
    configuration?: TableOfContents.IConfig
  ): TableOfContentsModel<H, W> {
    const model = this._createNew(widget, configuration);

    const context = widget.context;

    const updateHeadings = () => {
      model.refresh().catch(reason => {
        console.error('Failed to update the table of contents.', reason);
      });
    };
    const monitor = new ActivityMonitor({
      signal: context.model.contentChanged,
      timeout: RENDER_TIMEOUT
    });
    monitor.activityStopped.connect(updateHeadings);

    const updateTitle = () => {
      model.title = PathExt.basename(context.localPath);
    };
    context.pathChanged.connect(updateTitle);

    context.ready
      .then(() => {
        updateTitle();
        updateHeadings();
      })
      .catch(reason => {
        console.error(`Failed to initiate headings for ${context.localPath}.`);
      });

    widget.disposed.connect(() => {
      monitor.activityStopped.disconnect(updateHeadings);
      context.pathChanged.disconnect(updateTitle);
    });

    return model;
  }

  /**
   * Abstract table of contents model instantiation to allow
   * override by real implementation to customize it. The public
   * `createNew` contains the signal connections standards for IDocumentWidget
   * when the model has been instantiated.
   *
   * @param widget
   * @param configuration
   */
  protected abstract _createNew(
    widget: W,
    configuration?: TableOfContents.IConfig
  ): TableOfContentsModel<H, W>;
}
// -x-
// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { VDomModel } from '@jupyterlab/ui-components';
import { JSONExt } from '@lumino/coreutils';
import { ISignal, Signal } from '@lumino/signaling';
import { Widget } from '@lumino/widgets';
import { TableOfContents } from './tokens';
// -x-
/**
 * Abstract table of contents model.

/**
 * Constructor
 *
 * @param widget The widget to search in
 * @param configuration Default model configuration
 */
constructor(
protected widget: T,
configuration?: TableOfContents.IConfig
) {
super();
this._activeHeading = null;
this._activeHeadingChanged = new Signal<
    TableOfContentsModel<H, T>,
    H | null
>(this);
this._collapseChanged = new Signal<TableOfContentsModel<H, T>, H>(this);
this._configuration = configuration ?? { ...TableOfContents.defaultConfig };
this._headings = new Array<H>();
this._headingsChanged = new Signal<TableOfContentsModel<H, T>, void>(this);
this._isActive = false;
this._isRefreshing = false;
this._needsRefreshing = false;
}
// -x-
/**
 * Current active entry.
 *
 * @returns table of contents active entry
 */
get activeHeading(): H | null {
return this._activeHeading;
}
// -x-
/**
 * Signal emitted when the active heading changes.
 */
get activeHeadingChanged(): ISignal<TableOfContents.IModel<H>, H | null> {
return this._activeHeadingChanged;
}
// -x-
/**
 * Signal emitted when a table of content section collapse state changes.
 */
get collapseChanged(): ISignal<TableOfContents.IModel<H>, H | null> {
return this._collapseChanged;
}
// -x-
/**
 * Model configuration
 */
get configuration(): TableOfContents.IConfig {
return this._configuration;
}
// -x-
/**
 * Type of document supported by the model.
 *
 * #### Notes
 * A `data-document-type` attribute with this value will be set
 * on the tree view `.jp-TableOfContents-content[data-document-type="..."]`
 */
abstract readonly documentType: string;

/**
 * List of headings.
 *
 * @returns table of contents list of headings
 */
get headings(): H[] {
return this._headings;
}
// -x-
/**
 * Signal emitted when the headings changes.
 */
get headingsChanged(): ISignal<TableOfContents.IModel<H>, void> {
return this._headingsChanged;
}

/**
 * Whether the model is active or not.
 *
 * #### Notes
 * An active model means it is displayed in the table of contents.
 * This can be used by subclass to limit updating the headings.
 */
get isActive(): boolean {
return this._isActive;
}
set isActive(v: boolean) {
this._isActive = v;
// Refresh on activation expect if it is always active
//  => a ToC model is always active e.g. when displaying numbering in the document
if (this._isActive && !this.isAlwaysActive) {
    this.refresh().catch(reason => {
    console.error('Failed to refresh ToC model.', reason);
    });
}
}
// -x-
/**
 * Whether the model gets updated even if the table of contents panel
 * is hidden or not.
 *
 * #### Notes
 * For example, ToC models use to add title numbering will
 * set this to true.
 */
protected get isAlwaysActive(): boolean {
return false;
}

/**
     this.refresh().catch(reason => {
    console.error('Failed to update the table of contents.', reason);
    });
}
}
// -x-
/**
 * Callback on heading collapse.
 *
 * @param options.heading The heading to change state (all headings if not provided)
 * @param options.collapsed The new collapsed status (toggle existing status if not provided)
 */
toggleCollapse(options: { heading?: H; collapsed?: boolean }): void {
if (options.heading) {
    options.heading.collapsed =
    options.collapsed ?? !options.heading.collapsed;
    this.stateChanged.emit();
    this._collapseChanged.emit(options.heading);
} else {
    // Use the provided state or collapsed all except if all are collapsed
    const newState =
    options.collapsed ?? !this.headings.some(h => !(h.collapsed ?? false));
    this.headings.forEach(h => (h.collapsed = newState));
    this.stateChanged.emit();
    this._collapseChanged.emit(null);
}
}
// -x-
/**
 * Test if two headings are equal or not.
 *
 * @param heading1 First heading
 * @param heading2 Second heading
 * @returns Whether the headings are equal.
 */
protected isHeadingEqual(heading1: H, heading2: H): boolean {
return (
    heading1.level === heading2.level &&
    heading1.text === heading2.text &&
    heading1.prefix === heading2.prefix
);
}
// -x-
/**
 * Test if two list of headings are equal or not.
 *
 * @param headings1 First list of headings
 * @param headings2 Second list of headings
 * @returns Whether the array are equal.
 */
private _areHeadingsEqual(headings1: H[], headings2: H[]): boolean {
if (headings1.length === headings2.length) {
    for (let i = 0; i < headings1.length; i++) {
    if (!this.isHeadingEqual(headings1[i], headings2[i])) {
        return false;
    }
    }
    return true;
}

return false;
}
// -x-
export interface ITableOfContentsTreeProps {
    /**
     * Currently active heading.
     */
    activeHeading: TableOfContents.IHeading | null;
    /**
     * Type of document supported by the model.
     */
    documentType: string;
    /**
     * List of headings to render.
     */
    headings: TableOfContents.IHeading[];
    /**
     * Set active heading.
     */
    setActiveHeading: (heading: TableOfContents.IHeading) => void;
    /**
     * Collapse heading callback.
     */
    onCollapseChange: (heading: TableOfContents.IHeading) => void;
  }
// -x-
/**
 * React component for a table of contents tree.
 */
export class TableOfContentsTree extends React.PureComponent<ITableOfContentsTreeProps> {
/**
 * Renders a table of contents tree.
 */
render(): JSX.Element {
    const { documentType } = this.props;
    return (
    <ol
        className="jp-TableOfContents-content"
        {...{ 'data-document-type': documentType }}
    >
        {this.buildTree()}
    </ol>
    );
}

/**
 * Convert the flat headings list to a nested tree list
 */
protected buildTree(): JSX.Element[] {
    if (this.props.headings.length === 0) {
    return [];
    }

    const buildOneTree = (currentIndex: number): [JSX.Element, number] => {
    const items = this.props.headings;
    const children = new Array<JSX.Element>();
    const current = items[currentIndex];
    let nextCandidateIndex = currentIndex + 1;

    while (nextCandidateIndex < items.length) {
        const candidateItem = items[nextCandidateIndex];
        if (candidateItem.level <= current.level) {
        break;
        }
        const [child, nextIndex] = buildOneTree(nextCandidateIndex);
        children.push(child);
        nextCandidateIndex = nextIndex;
    }
    const currentTree = (
        <TableOfContentsItem
        key={`${current.level}-${currentIndex}-${current.text}`}
        isActive={
            !!this.props.activeHeading && current === this.props.activeHeading
        }
        heading={current}
        onMouseDown={this.props.setActiveHeading}
        onCollapse={this.props.onCollapseChange}
        >
        {children.length ? children : null}
        </TableOfContentsItem>
    );
    return [currentTree, nextCandidateIndex];
    };

    const trees = new Array<JSX.Element>();
    let currentIndex = 0;
    while (currentIndex < this.props.headings.length) {
    const [tree, nextIndex] = buildOneTree(currentIndex);
    trees.push(tree);
    currentIndex = nextIndex;
    }

    return trees;
}
}
// -x-
import {
    ILabShell,
    ILayoutRestorer,
    JupyterFrontEnd,
    JupyterFrontEndPlugin
  } from '@jupyterlab/application';
  import { ISettingRegistry } from '@jupyterlab/settingregistry';
  import {
    ITableOfContentsRegistry,
    ITableOfContentsTracker,
    TableOfContents,
    TableOfContentsPanel,
    TableOfContentsRegistry,
    TableOfContentsTracker
  } from '@jupyterlab/toc';
  import { ITranslator, nullTranslator } from '@jupyterlab/translation';
  import {
    collapseAllIcon,
    CommandToolbarButton,
    ellipsesIcon,
    expandAllIcon,
    MenuSvg,
    numberingIcon,
    tocIcon,
    Toolbar,
    ToolbarButton
  } from '@jupyterlab/ui-components';
// -x-
  /**
   * A namespace for command IDs of table of contents plugin.
   */
  namespace CommandIDs {
    export const displayNumbering = 'toc:display-numbering';
  
    export const displayH1Numbering = 'toc:display-h1-numbering';
  
    export const displayOutputNumbering = 'toc:display-outputs-numbering';
  
    export const showPanel = 'toc:show-panel';
  
    export const toggleCollapse = 'toc:toggle-collapse';
  }
// -x-

const trans = (translator ?? nullTranslator).load('jupyterlab');
let configuration = { ...TableOfContents.defaultConfig };

// Create the ToC widget:
const toc = new TableOfContentsPanel(translator ?? undefined);
toc.title.icon = tocIcon;
toc.title.caption = trans.__('Table of Contents');
toc.id = 'table-of-contents';
toc.node.setAttribute('role', 'region');
toc.node.setAttribute('aria-label', trans.__('Table of Contents section'));
// -x-
app.commands.addCommand(CommandIDs.displayH1Numbering, {
    label: trans.__('Show first-level heading number'),
    execute: () => {
    if (toc.model) {
        toc.model.setConfiguration({
        numberingH1: !toc.model.configuration.numberingH1
        });
    }
    },
    isEnabled: () =>
    toc.model?.supportedOptions.includes('numberingH1') ?? false,
    isToggled: () => toc.model?.configuration.numberingH1 ?? false
});
// -x-
app.commands.addCommand(CommandIDs.displayNumbering, {
    label: trans.__('Show heading number in the document'),
    icon: args => (args.toolbar ? numberingIcon : undefined),
    execute: () => {
    if (toc.model) {
        toc.model.setConfiguration({
        numberHeaders: !toc.model.configuration.numberHeaders
        });
        app.commands.notifyCommandChanged(CommandIDs.displayNumbering);
    }
    },
    isEnabled: () =>
    toc.model?.supportedOptions.includes('numberHeaders') ?? false,
    isToggled: () => toc.model?.configuration.numberHeaders ?? false
});
// -x-
app.commands.addCommand(CommandIDs.displayOutputNumbering, {
    label: trans.__('Show output headings'),
    execute: () => {
    if (toc.model) {
        toc.model.setConfiguration({
        includeOutput: !toc.model.configuration.includeOutput
        });
    }
    },
    isEnabled: () =>
    toc.model?.supportedOptions.includes('includeOutput') ?? false,
    isToggled: () => toc.model?.configuration.includeOutput ?? false
});
// -x-
app.commands.addCommand(CommandIDs.showPanel, {
    label: trans.__('Table of Contents'),
    execute: () => {
    app.shell.activateById(toc.id);
    }
});
// -x-
function someExpanded(model: TableOfContents.Model): boolean {
    /*
    * @private
    */
    function onConnect() {
        let widget = app.shell.currentWidget;
        if (!widget) {
        return;
        }
        let model = tracker.get(widget);
        if (!model) {
        model = tocRegistry.getModel(widget, configuration) ?? null;
        if (model) {
            tracker.add(widget, model);
        }

        widget.disposed.connect(() => {
            model?.dispose();
        });
        }

        if (toc.model) {
        toc.model.headingsChanged.disconnect(onCollapseChange);
        toc.model.collapseChanged.disconnect(onCollapseChange);
        }

        toc.model = model;
        if (toc.model) {
        toc.model.headingsChanged.connect(onCollapseChange);
        toc.model.collapseChanged.connect(onCollapseChange);
        }
        setToolbarButtonsState();
    }

    function setToolbarButtonsState() {
        app.commands.notifyCommandChanged(CommandIDs.displayNumbering);
        app.commands.notifyCommandChanged(CommandIDs.toggleCollapse);
    }

    function onCollapseChange() {
        app.commands.notifyCommandChanged(CommandIDs.toggleCollapse);
    }
}
// -x-
  /**
 * Table of contents registry plugin.
 */
const registry: JupyterFrontEndPlugin<ITableOfContentsRegistry> = {
id: '@jupyterlab/toc-extension:registry',
description: 'Provides the table of contents registry.',
autoStart: true,
provides: ITableOfContentsRegistry,
activate: (): ITableOfContentsRegistry => {
    // Create the ToC registry
    return new TableOfContentsRegistry();
}
};
// -x-
/**
 * Table of contents tracker plugin.
 */
const tracker: JupyterFrontEndPlugin<ITableOfContentsTracker> = {
id: '@jupyterlab/toc-extension:tracker',
description: 'Adds the table of content widget and provides its tracker.',
autoStart: true,
provides: ITableOfContentsTracker,
requires: [ITableOfContentsRegistry],
optional: [ITranslator, ILayoutRestorer, ILabShell, ISettingRegistry],
activate: activateTOC
};

/**
 * Exports.
 */
export default [registry, tracker];
// -x-
export class TableOfContentsTracker implements ITableOfContentsTracker {
    /**
     * Constructor
     */
    constructor() {
      this.modelMapping = new WeakMap<Widget, TableOfContents.Model>();
    }
  
    /**
     * Track a given model.
     *
     * @param widget Widget
     * @param model Table of contents model
     */
    add(widget: Widget, model: TableOfContents.Model): void {
      this.modelMapping.set(widget, model);
    }
  
    /**
     * Get the table of contents model associated with a given widget.
     *
     * @param widget Widget
     * @returns The table of contents model
     */
    get(widget: Widget): TableOfContents.Model | null {
      const model = this.modelMapping.get(widget);
  
      return !model || model.isDisposed ? null : model;
    }
  
    protected modelMapping: WeakMap<Widget, TableOfContents.Model>;
  }
//-x-
// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { HoverBox } from '@jupyterlab/ui-components';
import { CodeEditor } from '@jupyterlab/codeeditor';
import {
  IRenderMime,
  IRenderMimeRegistry,
  MimeModel
} from '@jupyterlab/rendermime';
import { JSONObject } from '@lumino/coreutils';
import { Message } from '@lumino/messaging';
import { PanelLayout, Widget } from '@lumino/widgets';

/**
 * The class name added to each tooltip.
 */
const TOOLTIP_CLASS = 'jp-Tooltip';

/**
 * The class name added to the tooltip content.
 */
const CONTENT_CLASS = 'jp-Tooltip-content';

/**
 * The class added to the body when a tooltip exists on the page.
 */
const BODY_CLASS = 'jp-mod-tooltip';

/**
 * The minimum height of a tooltip widget.
 */
const MIN_HEIGHT = 20;

/**
 * The maximum height of a tooltip widget.
 */
const MAX_HEIGHT = 250;

/**
 * A flag to indicate that event handlers are caught in the capture phase.
 */
const USE_CAPTURE = true;

/**
 * A tooltip widget.
 */
export class Tooltip extends Widget {
  /**
   * Instantiate a tooltip.
   */
  constructor(options: Tooltip.IOptions) {
    super();

    const layout = (this.layout = new PanelLayout());
    const model = new MimeModel({ data: options.bundle });

    this.anchor = options.anchor;
    this.addClass(TOOLTIP_CLASS);
    this.hide();
    this._editor = options.editor;
    this._position = options.position;
    this._rendermime = options.rendermime;

    const mimeType = this._rendermime.preferredMimeType(options.bundle, 'any');

    if (!mimeType) {
      return;
    }

    this._content = this._rendermime.createRenderer(mimeType);
    this._content
      .renderModel(model)
      .then(() => this._setGeometry())
      .catch(error => console.error('tooltip rendering failed', error));
    this._content.addClass(CONTENT_CLASS);
    layout.addWidget(this._content);
  }

  /**
   * The anchor widget that the tooltip widget tracks.
   */
  readonly anchor: Widget;

  /**
   * Dispose of the resources held by the widget.
   */
  dispose(): void {
    if (this._content) {
      this._content.dispose();
      this._content = null;
    }
    super.dispose();
  }

  /**
   * Handle the DOM events for the widget.
   *
   * @param event - The DOM event sent to the widget.
   *
   * #### Notes
   * This method implements the DOM `EventListener` interface and is
   * called in response to events on the dock panel's node. It should
   * not be called directly by user code.
   */
  handleEvent(event: Event): void {
    if (this.isHidden || this.isDisposed) {
      return;
    }

    const { node } = this;
    const target = event.target as HTMLElement;

    switch (event.type) {
      case 'keydown':
        if (node.contains(target)) {
          return;
        }
        this.dispose();
        break;
      case 'mousedown':
        if (node.contains(target)) {
          this.activate();
          return;
        }
        this.dispose();
        break;
      case 'scroll':
        this._evtScroll(event as MouseEvent);
        break;
      default:
        break;
    }
  }

  /**
   * Handle `'activate-request'` messages.
   */
  protected onActivateRequest(msg: Message): void {
    this.node.tabIndex = 0;
    this.node.focus();
  }

  /**
   * Handle `'after-attach'` messages.
   */
  protected onAfterAttach(msg: Message): void {
    document.body.classList.add(BODY_CLASS);
    document.addEventListener('keydown', this, USE_CAPTURE);
    document.addEventListener('mousedown', this, USE_CAPTURE);
    this.anchor.node.addEventListener('scroll', this, USE_CAPTURE);
    this.update();
  }

  /**
   * Handle `before-detach` messages for the widget.
   */
  protected onBeforeDetach(msg: Message): void {
    document.body.classList.remove(BODY_CLASS);
    document.removeEventListener('keydown', this, USE_CAPTURE);
    document.removeEventListener('mousedown', this, USE_CAPTURE);
    this.anchor.node.removeEventListener('scroll', this, USE_CAPTURE);
  }

  /**
   * Handle `'update-request'` messages.
   */
  protected onUpdateRequest(msg: Message): void {
    if (this.isHidden) {
      this.show();
    }
    this._setGeometry();
    super.onUpdateRequest(msg);
  }

  /**
   * Handle scroll events for the widget
   */
  private _evtScroll(event: MouseEvent) {
    // All scrolls except scrolls in the actual hover box node may cause the
    // referent editor that anchors the node to move, so the only scroll events
    // that can safely be ignored are ones that happen inside the hovering node.
    if (this.node.contains(event.target as HTMLElement)) {
      return;
    }

    this.update();
  }

  /**
   * Find the position of the first character of the current token.
   */
  private _getTokenPosition(): CodeEditor.IPosition | undefined {
    const editor = this._editor;
    const cursor = editor.getCursorPosition();
    const end = editor.getOffsetAt(cursor);
    const line = editor.getLine(cursor.line);

    if (!line) {
      return;
    }

    const tokens = line.substring(0, end).split(/\W+/);
    const last = tokens[tokens.length - 1];
    const start = last ? end - last.length : end;
    return editor.getPositionAt(start);
  }

  /**
   * Set the geometry of the tooltip widget.
   */
  private _setGeometry(): void {
    // determine position for hover box placement
    const position = this._position ? this._position : this._getTokenPosition();

    if (!position) {
      return;
    }

    const editor = this._editor;

    const anchor = editor.getCoordinateForPosition(position);

    if (!anchor) {
      return;
    }

    const style = window.getComputedStyle(this.node);
    const paddingLeft = parseInt(style.paddingLeft!, 10) || 0;

    const host =
      (editor.host.closest('.jp-MainAreaWidget > .lm-Widget') as HTMLElement) ||
      editor.host;

    // Calculate the geometry of the tooltip.
    HoverBox.setGeometry({
      anchor,
      host,
      maxHeight: MAX_HEIGHT,
      minHeight: MIN_HEIGHT,
      node: this.node,
      offset: { horizontal: -1 * paddingLeft },
      privilege: 'below',
      outOfViewDisplay: {
        top: 'stick-inside',
        bottom: 'stick-inside'
      },
      style: style
    });
  }

  private _content: IRenderMime.IRenderer | null = null;
  private _editor: CodeEditor.IEditor;
  private _position: CodeEditor.IPosition | undefined;
  private _rendermime: IRenderMimeRegistry;
}

/**
 * A namespace for tooltip widget statics.
 */
export namespace Tooltip {
  /**
   * Instantiation options for a tooltip widget.
   */
  export interface IOptions {
    /**
     * The anchor widget that the tooltip widget tracks.
     */
    anchor: Widget;

    /**
     * The data that populates the tooltip widget.
     */
    bundle: JSONObject;

    /**
     * The editor referent of the tooltip model.
     */
    editor: CodeEditor.IEditor;

    /**
     * The rendermime instance used by the tooltip model.
     */
    rendermime: IRenderMimeRegistry;

    /**
     * Position at which the tooltip should be placed.
     *
     * If not given, the position of the first character
     * in the current token will be used.
     */
    position?: CodeEditor.IPosition;
  }
}
// -x-

import { CodeEditor } from '@jupyterlab/codeeditor';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Kernel } from '@jupyterlab/services';
import { Token } from '@lumino/coreutils';
import { Widget } from '@lumino/widgets';

/**
 * The tooltip manager token.
 */
export const ITooltipManager = new Token<ITooltipManager>(
  '@jupyterlab/tooltip:ITooltipManager',
  'A service for the tooltip manager for the application. Use this to allow your extension to invoke a tooltip.'
);

/**
 * A manager to register tooltips with parent widgets.
 */
export interface ITooltipManager {
  /**
   * Invoke a tooltip.
   */
  invoke(options: ITooltipManager.IOptions): void;
}

/**
 * A namespace for `ITooltipManager` interface specifications.
 */
export namespace ITooltipManager {
  /**
   * An interface for tooltip-compatible objects.
   */
  export interface IOptions {
    /**
     * The referent anchor the tooltip follows.
     */
    readonly anchor: Widget;

    /**
     * The referent editor for the tooltip.
     */
    readonly editor: CodeEditor.IEditor;

    /**
     * The kernel the tooltip communicates with to populate itself.
     */
    readonly kernel: Kernel.IKernelConnection;

    /**
     * The renderer the tooltip uses to render API responses.
     */
    readonly rendermime: IRenderMimeRegistry;
  }
// -x-
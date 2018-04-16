declare module 'gnat' {
    // Valid values are:
    //
    //  * NO_CODE
    //  * COVERED
    //  * NOT_COVERED
    //  * PARTIALLY_COVERED
    type CoverageStatus = string;

    export interface ICoverage {
        hits: number;
        status: CoverageStatus;
    }

    // **
    //  Part for the filter.json (filter-panel)
    // **

    // Create the property for any filter category
    export interface IFilter {
        _message_count: number;
        _ui_unselected?: boolean;
        _ui_selected_message_count: number;
    }

    // Create the property for the tool filter
    export interface ITool {
        id: number;
        name: string;
    }

    // Create the property for the rule filter
    export interface IRule {
        id: number;
        name: string;
        tool_id: number;
    }

    // Create the property for the property filter
    export interface IProperty {
        id: number;
        name: string;
        tool_id: number;
    }

    // Create the property for the ranking filter
    export interface IRanking {
        id: number;
        name: string;
        tool_id: number;
    }

    // Now concats the propert for filters and for specific filter
    export interface IRuleFilter extends IRule, IFilter {}
    export interface IToolFilter extends ITool, IFilter {}
    export interface IPropertyFilter extends IProperty, IFilter {}
    export interface IRankingFilter extends IRanking, IFilter {}

    // Define the model for the filter object
    export interface IFilterIndex {
        project: string;
        creation_time: number;
        tools: [ IToolFilter ];
        rules: [ IRuleFilter ];
        properties: [ IPropertyFilter ];
        ranking: [ IRankingFilter ];
        message_count?: { [toolId: number]: number };
        _total_message_count: number;
        _database: string;
    }

    // **
    //  Part for the code.json (code-navigation)
    // **

    export interface ISource {
        filename: string;
        coverage?: number;
        message_count?: { [toolId: number]: number };
        _total_message_count: number;
        _ui_total_message_count?: number;
    }

    export interface ISourceDir {
        name: string;
        message_count?: { [toolId: number]: number };
        coverage?: number;
        _total_message_count: number;
        _ui_total_message_count?: number;
        sources: [ ISource ];
    }

    export interface IModule {
        name: string;
        message_count?: { [toolId: number]: number };
        _total_message_count: number;
        _ui_total_message_count?: number;
        _source_dirs_common_prefix: string;
        coverage?: number;
        source_dirs: [ ISourceDir ];
    }

    export interface ICodeIndex {
        modules: [ IModule ];
    }

    // **
    //  Part for the message.json (message-navigation)
    // **

    export interface IMessage {
        id: number;
        col_begin: number;
        col_end: number;
        line: number;
        name: string;
        properties: IProperty[];
        rule: IRule;
        ranking: IRanking;
    }

    export interface ISourceNav {
        filename: string;
        source_dir: string;
        full_path: string;
        coverage?: number;
        message_count?: { [toolId: number]: number };
        _messages?: IMessage[];
        // expanded ?
        _total_message_count: number;
        _ui_total_message_count?: number;
    }

    export interface IMessageIndex {
        sources: [ ISourceNav ];
        _ui_total_message_count?: number;
    }

    // **
    //  Part for the FILENAME.json (annotated-source)
    // **

    // **
    //  OLD PART, TO CLEAN AFTER TEST
    // **

    export interface IOLDRule {
        id: number;
        name: string;
        tool: IOLDTool;
    }
    export interface IOLDTool {
        id: number;
        name: string;
        tool_id: number;
    }
    export interface IOLDProperty {
        id: number;
        name: string;
        tool_id: number;
    }

    export interface IOLDRuleFilter extends IOLDRule, IFilter {}
    export interface IOLDToolFilter extends IOLDTool, IFilter {}
    export interface IOLDPropertyFilter extends IOLDProperty, IFilter {}

    export interface IMetric {
        rule: IOLDRule;
        value: string;
    }

    // Annotated source file

    export interface IAnnotatedSourceMessage {
        begin: number;
        end: number;
        rule: IRule;
        line: number;
        properties: IProperty[];
        text: string;
        _ui_hidden?: boolean;
    }

    export interface IAnnotatedSourceLine {
        number: number;
        content: string;
        html_content: string;
    }

    export interface IAnnotatedSourceFile {
        project: string;
        filename: string;
        source_dir: string;
        full_path: string;
        lines: IAnnotatedSourceLine[];
        metrics?: Array<{ [metricId: number]: IMetric }>;
        coverage?: { [line: number]: ICoverage };
        messages?: IAnnotatedSourceMessage[];
    }

}

# Own vendor-neutral Trajectory format, with OpenTelemetry/OpenInference only at the edges

Assayer defines its own small Trajectory model (ordered Steps with an optional `parent_id`) as the source of truth, instead of building on OpenTelemetry GenAI or OpenInference. Neither defines a trajectory object, scores, references or dataset linkage, and OTel GenAI is still in Development status. Langfuse and LangSmith also prefer their own namespaces over `gen_ai.*`. OTel/OpenInference conversion stays an optional import/export edge, so the core keeps no OTel dependency.

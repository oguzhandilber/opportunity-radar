import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  ExternalLink,
  Loader2,
  Save,
  X,
  Play,
  Trash2,
  Sparkles,
  DollarSign,
  TrendingUp,
  Target,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import clsx from "clsx";
import {
  useOpportunity,
  useUpdateOpportunity,
  useDeleteOpportunity,
  useAnalyzeOpportunity,
} from "../hooks/useApi";
import ScoreDisplay, { ScoreBar } from "../components/ScoreDisplay";

/**
 * Mission Control Brutalism Opportunity Detail
 *
 * Two-column tactical layout
 * Dark theme with signal colors
 */
export default function OpportunityDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: opportunity, isLoading } = useOpportunity(Number(id));
  const updateMutation = useUpdateOpportunity();
  const deleteMutation = useDeleteOpportunity();
  const analyzeMutation = useAnalyzeOpportunity();

  const handleStatusChange = (status: string) => {
    if (!opportunity) return;
    updateMutation.mutate({ id: opportunity.id, data: { status } });
  };

  const handleStartWorking = async () => {
    if (!opportunity) return;
    updateMutation.mutate({
      id: opportunity.id,
      data: { status: "in_progress" },
    });
    analyzeMutation.mutate(opportunity.id);
  };

  const handleDelete = () => {
    if (!opportunity) return;
    if (confirm("Are you sure you want to delete this opportunity?")) {
      deleteMutation.mutate(opportunity.id, {
        onSuccess: () => navigate("/opportunities"),
      });
    }
  };

  const isAnalyzing = analyzeMutation.isPending;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-radar-500" />
          <span className="font-mono text-sm text-text-secondary">
            LOADING TARGET...
          </span>
        </div>
      </div>
    );
  }

  if (!opportunity) {
    return (
      <div className="bg-dark border border-light p-12 text-center">
        <p className="font-mono text-text-secondary">TARGET NOT FOUND</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate(-1)}
          className="p-2 hover:bg-medium text-text-secondary hover:text-text-primary transition-colors"
          aria-label="Go back"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={clsx("badge", `badge-${opportunity.status}`)}>
              {opportunity.status.replace("_", " ").toUpperCase()}
            </span>
            {opportunity.product_type && (
              <span className="badge badge-sector">
                {opportunity.product_type.toUpperCase()}
              </span>
            )}
            {opportunity.sector && (
              <span className="badge badge-sector">
                {opportunity.sector.toUpperCase()}
              </span>
            )}
          </div>
          <h1 className="text-xl font-body font-semibold text-text-primary">
            {opportunity.title}
          </h1>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => handleStatusChange("saved")}
          disabled={opportunity.status === "saved"}
          className={clsx(
            "btn flex items-center gap-2 min-h-[44px]",
            opportunity.status === "saved"
              ? "btn-secondary opacity-50"
              : "btn-primary",
          )}
        >
          <Save className="w-4 h-4" />
          SAVE
        </button>
        <button
          onClick={handleStartWorking}
          disabled={isAnalyzing}
          className={clsx(
            "btn flex items-center gap-2 min-h-[44px]",
            isAnalyzing ? "btn-primary" : "btn-secondary",
          )}
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <Sparkles className="w-4 h-4" />
              ANALYZING...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <Sparkles className="w-4 h-4" />
              DEEP ANALYSIS
            </>
          )}
        </button>
        <button
          onClick={() => handleStatusChange("rejected")}
          disabled={opportunity.status === "rejected"}
          className={clsx(
            "btn flex items-center gap-2 min-h-[44px]",
            opportunity.status === "rejected"
              ? "btn-secondary opacity-50"
              : "btn-secondary",
          )}
        >
          <X className="w-4 h-4" />
          REJECT
        </button>
        <div className="flex-1" />
        <button
          onClick={handleDelete}
          className="btn btn-danger flex items-center gap-2 min-h-[44px]"
        >
          <Trash2 className="w-4 h-4" />
          DELETE
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Summary */}
          <div className="bg-dark border border-light p-6">
            <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
              SUMMARY
            </h2>
            <p className="font-body text-text-secondary">
              {opportunity.summary || "No summary available"}
            </p>
          </div>

          {/* Original Source */}
          {opportunity.source_content && (
            <div className="bg-dark border border-light p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-mono font-bold text-text-primary tracking-wider">
                  ORIGINAL SOURCE
                </h2>
                {opportunity.source_url && (
                  <a
                    href={opportunity.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-radar-500 hover:text-radar-400 font-mono text-sm"
                  >
                    VIEW <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
              <div className="bg-darkest border border-light p-4">
                <p className="font-body text-sm text-text-secondary whitespace-pre-wrap">
                  {opportunity.source_content}
                </p>
                <div className="flex gap-4 mt-4 font-mono text-xs text-text-tertiary">
                  {opportunity.source && (
                    <span>SOURCE: {opportunity.source.toUpperCase()}</span>
                  )}
                  {opportunity.source_author && (
                    <span>AUTHOR: {opportunity.source_author}</span>
                  )}
                  {opportunity.source_engagement !== undefined && (
                    <span>ENGAGEMENT: {opportunity.source_engagement}</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* AI Analysis Notes */}
          {opportunity.notes && (
            <div className="bg-signal-violet/10 border-2 border-signal-violet/50 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-5 h-5 text-signal-violet" />
                <h2 className="font-mono font-bold text-signal-violet tracking-wider">
                  AI ANALYSIS
                </h2>
              </div>
              <p className="font-body text-text-primary whitespace-pre-wrap">
                {opportunity.notes}
              </p>
            </div>
          )}

          {/* Competitors */}
          {opportunity.competitors && opportunity.competitors.length > 0 && (
            <div className="bg-dark border border-light p-6">
              <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
                COMPETITORS
              </h2>
              <div className="space-y-3">
                {opportunity.competitors.map((comp, i) => (
                  <div key={i} className="bg-darkest border border-light p-4">
                    <div className="flex items-start justify-between">
                      <div className="font-mono font-bold text-text-primary">
                        {comp.name}
                      </div>
                      {comp.url && (
                        <a
                          href={comp.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-radar-500 hover:text-radar-400"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                    {comp.strengths && (
                      <p className="font-body text-sm text-signal-success mt-2">
                        <span className="font-mono text-xs">STRENGTHS:</span>{" "}
                        {comp.strengths}
                      </p>
                    )}
                    {comp.weaknesses && (
                      <p className="font-body text-sm text-signal-critical mt-1">
                        <span className="font-mono text-xs">WEAKNESSES:</span>{" "}
                        {comp.weaknesses}
                      </p>
                    )}
                    {comp.notes && (
                      <p className="font-body text-sm text-text-secondary mt-1">
                        {comp.notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggested Features */}
          {opportunity.suggested_features &&
            opportunity.suggested_features.length > 0 && (
              <div className="bg-dark border border-light p-6">
                <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
                  SUGGESTED FEATURES
                </h2>
                <div className="space-y-3">
                  {opportunity.suggested_features.map((feat, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-3 border-l-2 border-l-light pl-4"
                    >
                      <span
                        className={clsx(
                          "badge border",
                          feat.priority === "high"
                            ? "bg-signal-critical/20 text-signal-critical border-signal-critical/50"
                            : feat.priority === "medium"
                              ? "bg-signal-warning/20 text-signal-warning border-signal-warning/50"
                              : "bg-medium text-text-secondary border-light",
                        )}
                      >
                        {feat.priority?.toUpperCase() || "LOW"}
                      </span>
                      <div className="flex-1">
                        <div className="font-body font-medium text-text-primary">
                          {feat.feature}
                        </div>
                        {feat.description && (
                          <p className="font-body text-sm text-text-secondary mt-1">
                            {feat.description}
                          </p>
                        )}
                      </div>
                      {feat.effort && (
                        <span className="font-mono text-xs text-text-tertiary bg-darkest px-2 py-1">
                          {feat.effort.toUpperCase()}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Go-to-Market Strategy */}
          {opportunity.go_to_market && (
            <div className="bg-dark border border-light p-6">
              <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
                GO-TO-MARKET STRATEGY
              </h2>
              <p className="font-body text-text-secondary whitespace-pre-wrap">
                {opportunity.go_to_market}
              </p>
            </div>
          )}
        </div>

        {/* Sidebar - 1 column */}
        <div className="space-y-6">
          {/* Scores */}
          <div className="bg-dark border border-light p-6">
            <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
              SCORES
            </h2>
            <div className="space-y-4">
              {/* Total Score */}
              <div className="text-center pb-4 border-b border-light">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <ScoreDisplay
                    score={opportunity.total_score}
                    size="lg"
                    showBar={false}
                  />
                  <span className="text-text-tertiary font-mono text-sm">
                    /10
                  </span>
                </div>
                <span className="label-mono">TOTAL SCORE</span>
                {opportunity.confidence && (
                  <p className="font-mono text-xs text-text-tertiary mt-2">
                    CONFIDENCE: {(opportunity.confidence * 100).toFixed(0)}%
                  </p>
                )}
              </div>

              {/* Component Scores */}
              <div className="space-y-3">
                <ScoreBar score={opportunity.demand_score} label="DEMAND" />
                <ScoreBar score={opportunity.market_score} label="MARKET" />
                <ScoreBar
                  score={opportunity.feasibility_score}
                  label="FEASIBLE"
                />
                <ScoreBar score={opportunity.revenue_score} label="REVENUE" />
              </div>
            </div>
          </div>

          {/* Details */}
          <div className="bg-dark border border-light p-6">
            <h2 className="font-mono font-bold text-text-primary tracking-wider mb-4">
              DETAILS
            </h2>
            <dl className="space-y-3">
              <DetailItem
                label="PRODUCT TYPE"
                value={opportunity.product_type || "--"}
              />
              <DetailItem label="SECTOR" value={opportunity.sector || "--"} />
              <DetailItem
                label="BUSINESS MODEL"
                value={opportunity.business_model || "--"}
              />
              <DetailItem
                label="CREATED"
                value={new Date(opportunity.created_at).toLocaleDateString()}
              />
            </dl>
          </div>

          {/* Payment Intent Analysis */}
          {(opportunity.payment_signal_tier ||
            opportunity.purchase_journey_stage) && (
            <div className="bg-signal-success/10 border-2 border-signal-success/50 p-6">
              <div className="flex items-center gap-2 mb-4">
                <DollarSign className="w-5 h-5 text-signal-success" />
                <h2 className="font-mono font-bold text-signal-success tracking-wider">
                  PAYMENT INTENT
                </h2>
              </div>
              <dl className="space-y-3">
                {opportunity.payment_signal_tier && (
                  <DetailItem
                    label="SIGNAL TIER"
                    value={
                      <span
                        className={clsx(
                          "badge border",
                          opportunity.payment_signal_tier === 1
                            ? "bg-signal-success/20 text-signal-success border-signal-success/50"
                            : opportunity.payment_signal_tier === 2
                              ? "bg-signal-info/20 text-signal-info border-signal-info/50"
                              : opportunity.payment_signal_tier === 3
                                ? "bg-signal-warning/20 text-signal-warning border-signal-warning/50"
                                : "bg-medium text-text-secondary border-light",
                        )}
                      >
                        TIER {opportunity.payment_signal_tier}
                      </span>
                    }
                  />
                )}
                {opportunity.purchase_journey_stage && (
                  <DetailItem
                    label="JOURNEY STAGE"
                    value={opportunity.purchase_journey_stage.toUpperCase()}
                  />
                )}
                {opportunity.monthly_price_estimate && (
                  <DetailItem
                    label="PRICE MENTIONED"
                    value={`$${opportunity.monthly_price_estimate}/MO`}
                    highlight
                  />
                )}
                {opportunity.revenue_potential_score && (
                  <DetailItem
                    label="REVENUE POTENTIAL"
                    value={`${opportunity.revenue_potential_score.toFixed(1)}/10`}
                  />
                )}
                {opportunity.churning_from &&
                  opportunity.churning_from.length > 0 && (
                    <DetailItem
                      label="CHURNING FROM"
                      value={opportunity.churning_from.join(", ")}
                      highlight
                    />
                  )}
              </dl>
            </div>
          )}

          {/* Success Prediction */}
          {(opportunity.success_prediction ||
            opportunity.pattern_match_score) && (
            <div className="bg-signal-info/10 border-2 border-signal-info/50 p-6">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-5 h-5 text-signal-info" />
                <h2 className="font-mono font-bold text-signal-info tracking-wider">
                  SUCCESS PREDICTION
                </h2>
              </div>
              <dl className="space-y-3">
                {opportunity.success_prediction && (
                  <DetailItem
                    label="SUCCESS PROBABILITY"
                    value={
                      <span
                        className={clsx(
                          "badge border",
                          opportunity.success_prediction >= 70
                            ? "bg-signal-success/20 text-signal-success border-signal-success/50"
                            : opportunity.success_prediction >= 40
                              ? "bg-signal-warning/20 text-signal-warning border-signal-warning/50"
                              : "bg-signal-critical/20 text-signal-critical border-signal-critical/50",
                        )}
                      >
                        {opportunity.success_prediction >= 70 && (
                          <CheckCircle className="w-3 h-3 mr-1" />
                        )}
                        {opportunity.success_prediction < 40 && (
                          <AlertTriangle className="w-3 h-3 mr-1" />
                        )}
                        {opportunity.success_prediction.toFixed(0)}%
                      </span>
                    }
                  />
                )}
                {opportunity.pattern_match_score && (
                  <DetailItem
                    label="PATTERN MATCH"
                    value={`${opportunity.pattern_match_score.toFixed(1)}/10`}
                  />
                )}
                {opportunity.risk_level && (
                  <DetailItem
                    label="RISK LEVEL"
                    value={
                      <span
                        className={clsx(
                          "badge border",
                          opportunity.risk_level === "low"
                            ? "bg-signal-success/20 text-signal-success border-signal-success/50"
                            : opportunity.risk_level === "medium"
                              ? "bg-signal-warning/20 text-signal-warning border-signal-warning/50"
                              : "bg-signal-critical/20 text-signal-critical border-signal-critical/50",
                        )}
                      >
                        {opportunity.risk_level.toUpperCase()}
                      </span>
                    }
                  />
                )}
                {opportunity.similar_successes &&
                  opportunity.similar_successes.length > 0 && (
                    <DetailItem
                      label="SIMILAR SUCCESSES"
                      value={opportunity.similar_successes
                        .slice(0, 3)
                        .join(", ")}
                    />
                  )}
              </dl>
            </div>
          )}

          {/* Niche Focus */}
          {opportunity.primary_niche && (
            <div className="bg-signal-violet/10 border-2 border-signal-violet/50 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Target className="w-5 h-5 text-signal-violet" />
                <h2 className="font-mono font-bold text-signal-violet tracking-wider">
                  NICHE FOCUS
                </h2>
              </div>
              <dl className="space-y-3">
                <DetailItem
                  label="PRIMARY NICHE"
                  value={
                    <span className="badge border bg-signal-violet/20 text-signal-violet border-signal-violet/50">
                      {opportunity.primary_niche
                        .replace(/_/g, " ")
                        .toUpperCase()}
                    </span>
                  }
                />
                {opportunity.niche_fit_score && (
                  <DetailItem
                    label="NICHE FIT"
                    value={`${opportunity.niche_fit_score.toFixed(1)}/10`}
                  />
                )}
                {opportunity.detected_niches &&
                  opportunity.detected_niches.length > 1 && (
                    <div>
                      <dt className="label-mono mb-2">OTHER NICHES</dt>
                      <dd className="flex flex-wrap gap-1">
                        {opportunity.detected_niches
                          .filter(
                            (n: { niche_id: string }) =>
                              n.niche_id !== opportunity.primary_niche,
                          )
                          .slice(0, 3)
                          .map(
                            (
                              n: {
                                niche_id: string;
                                niche_name: string;
                                confidence: number;
                              },
                              i: number,
                            ) => (
                              <span
                                key={i}
                                className="badge border bg-medium text-text-secondary border-light"
                              >
                                {n.niche_name.replace(/_/g, " ").toUpperCase()}
                              </span>
                            ),
                          )}
                      </dd>
                    </div>
                  )}
              </dl>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DetailItem({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <dt className="label-mono">{label}</dt>
      <dd
        className={clsx(
          "font-mono text-sm",
          highlight ? "text-signal-success font-bold" : "text-text-primary",
        )}
      >
        {value}
      </dd>
    </div>
  );
}

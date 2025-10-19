import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Download, Search, RefreshCw, Database, Cpu } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const APP_VERSION = "1.0.0";

interface HealthStatus {
  status?: string;
  model?: string;
  embedding_dim?: number;
  vectors_indexed?: number;
  total_images?: number;
  index_type?: string;
  device?: string;
}

interface SearchResult {
  rank: number;
  filename: string;
  image_path: string;
  similarity_score: number;
  confidence_percentage: string;
  num_query_matches: number;
}

interface SearchResponse {
  results: SearchResult[];
  timing_ms: number;
  enhanced_queries?: string[];
}

const Index = () => {
  const { toast } = useToast();
  const [health, setHealth] = useState<HealthStatus>({});
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.2);
  const [useEnhancement, setUseEnhancement] = useState(true);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isReloading, setIsReloading] = useState(false);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) throw new Error("Failed to fetch health status");
      const data = await response.json();
      setHealth(data);
    } catch (error) {
      console.error("Health check failed:", error);
      toast({
        title: "Connection Error",
        description: "Failed to connect to API",
        variant: "destructive",
      });
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) {
      toast({
        title: "Empty Query",
        description: "Please enter a search query",
        variant: "destructive",
      });
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          top_k: topK,
          threshold,
          use_enhancement: useEnhancement,
        }),
      });

      if (!response.ok) throw new Error("Search failed");
      const data = await response.json();
      setSearchResults(data);

      if (data.results.length === 0) {
        toast({
          title: "No Results",
          description: "Try lowering the threshold or adjusting your query",
        });
      }
    } catch (error) {
      console.error("Search failed:", error);
      toast({
        title: "Search Error",
        description: "Failed to execute search",
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  const handleReload = async () => {
    setIsReloading(true);
    try {
      const response = await fetch(`${API_BASE}/admin/reload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) throw new Error("Reload failed");
      const data = await response.json();

      toast({
        title: "Index Reloaded",
        description: `Completed in ${data.load_time_seconds?.toFixed(2)}s`,
      });

      fetchHealth();
    } catch (error) {
      console.error("Reload failed:", error);
      toast({
        title: "Reload Error",
        description: "Failed to reload index",
        variant: "destructive",
      });
    } finally {
      setIsReloading(false);
    }
  };

  const downloadCSV = () => {
    if (!searchResults?.results) return;

    const headers = ["Rank", "Filename", "Similarity Score", "Confidence", "Matches"];
    const rows = searchResults.results.map((r) => [
      r.rank,
      r.filename,
      r.similarity_score,
      r.confidence_percentage,
      r.num_query_matches,
    ]);

    const csv = [headers, ...rows].map((row) => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `search_results_${query.replace(/\s+/g, "_")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Helper function to get correct image URL
  const getImageUrl = (result: SearchResult) => {
    // If image_path already starts with /images/, use it directly with API_BASE
    if (result.image_path.startsWith('/images/')) {
      return `${API_BASE}${result.image_path}`;
    }
    // Otherwise, construct the URL using filename
    return `${API_BASE}/images/${result.filename}`;
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-80 border-r bg-card p-6 flex flex-col">
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-4">Search Parameters</h2>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="query">Query</Label>
              <Input
                id="query"
                placeholder="e.g., sunset over mountains"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="mt-1"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Enter natural language description
              </p>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="enhancement">Query Enhancement</Label>
              <Switch
                id="enhancement"
                checked={useEnhancement}
                onCheckedChange={setUseEnhancement}
              />
            </div>

            <div>
              <Label>Top K Results: {topK}</Label>
              <Slider
                value={[topK]}
                onValueChange={(v) => setTopK(v[0])}
                min={1}
                max={20}
                step={1}
                className="mt-2"
              />
            </div>

            <div>
              <Label>Score Threshold: {threshold.toFixed(2)}</Label>
              <Slider
                value={[threshold]}
                onValueChange={(v) => setThreshold(v[0])}
                min={0}
                max={0.6}
                step={0.01}
                className="mt-2"
              />
            </div>
          </div>

          <Separator className="my-6" />

          <Button
            onClick={handleSearch}
            disabled={isSearching}
            className="w-full"
            size="lg"
          >
            <Search className="mr-2 h-4 w-4" />
            {isSearching ? "Searching..." : "Search"}
          </Button>
        </div>

        <Separator className="my-6" />

        <div className="space-y-4 flex-1">
          <h3 className="text-sm font-semibold">System</h3>
          {health.vectors_indexed !== undefined && (
            <div className="text-sm space-y-1">
              <p className="text-muted-foreground">
                <span className="font-medium">Vectors:</span>{" "}
                {health.vectors_indexed.toLocaleString()}
              </p>
              <p className="text-muted-foreground">
                <span className="font-medium">Index:</span> {health.index_type || "N/A"}
              </p>
            </div>
          )}
          <Button
            onClick={handleReload}
            disabled={isReloading}
            variant="outline"
            className="w-full"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isReloading ? "animate-spin" : ""}`} />
            {isReloading ? "Reloading..." : "Reload Index"}
          </Button>
        </div>

        <Separator className="my-4" />

        <div className="text-center text-xs text-muted-foreground">
          Visual Semantic Search v{APP_VERSION}
          <br />
          API: {API_BASE}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        <div className="max-w-[1600px] mx-auto">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold mb-2">Visual Semantic Search</h1>
            {health.model && (
              <div className="flex items-center gap-4 text-sm">
                <span className="text-muted-foreground">
                  <strong>AI-Powered Image Retrieval</strong> | Model: {health.model} |
                  Images: {health.total_images?.toLocaleString() || 0}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    health.device === "cuda"
                      ? "bg-green-100 text-green-800"
                      : "bg-blue-100 text-blue-800"
                  }`}
                >
                  {health.device?.toUpperCase() || "N/A"}
                </span>
              </div>
            )}
          </div>

          <Separator className="mb-6" />

          {/* Tabs */}
          <Tabs defaultValue="results" className="w-full">
            <TabsList>
              <TabsTrigger value="results">Search Results</TabsTrigger>
              <TabsTrigger value="status">System Status</TabsTrigger>
            </TabsList>

            <TabsContent value="results" className="mt-6">
              {searchResults?.results && searchResults.results.length > 0 ? (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-xl font-semibold mb-4">
                      Top {searchResults.results.length} Results
                    </h2>

                    {/* Image Grid */}
                    <div className="grid grid-cols-5 gap-4">
                      {searchResults.results.map((result) => (
                        <Card key={result.rank} className="overflow-hidden">
                          <div className="aspect-square relative bg-muted">
                            <img
                              src={getImageUrl(result)}
                              alt={result.filename}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                console.error(`Failed to load image: ${getImageUrl(result)}`);
                                e.currentTarget.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f3f4f6'/%3E%3Ctext x='100' y='100' font-family='Arial' font-size='14' fill='%236b7280' text-anchor='middle' dy='0.3em'%3EImage not found%3C/text%3E%3C/svg%3E";
                              }}
                              onLoad={() => {
                                console.log(`Successfully loaded: ${getImageUrl(result)}`);
                              }}
                            />
                          </div>
                          <CardContent className="p-3">
                            <div className="text-center space-y-2">
                              <span
                                className={`inline-block px-3 py-1 rounded-full text-xs font-semibold text-white ${
                                  result.rank === 1
                                    ? "bg-red-500"
                                    : "bg-blue-500"
                                }`}
                              >
                                Rank #{result.rank}
                              </span>
                              <p className="font-semibold text-sm break-words">
                                {result.filename}
                              </p>
                              <div className="text-xs space-y-1 text-muted-foreground">
                                <p>
                                  <strong>Score:</strong>{" "}
                                  {result.similarity_score.toFixed(3)}
                                </p>
                                <p>Confidence: {result.confidence_percentage}</p>
                                <p>Matches: {result.num_query_matches}</p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  {/* Metrics */}
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Search Metrics</h3>
                    <div className="grid grid-cols-4 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm text-muted-foreground">
                            Search Time (ms)
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-2xl font-bold">
                            {searchResults.timing_ms.toFixed(1)}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm text-muted-foreground">
                            Top-1 Score
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-2xl font-bold">
                            {searchResults.results[0].similarity_score.toFixed(3)}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm text-muted-foreground">
                            Avg Score
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-2xl font-bold">
                            {(
                              searchResults.results.reduce(
                                (sum, r) => sum + r.similarity_score,
                                0
                              ) / searchResults.results.length
                            ).toFixed(3)}
                          </p>
                        </CardContent>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm text-muted-foreground">
                            Results Count
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-2xl font-bold">
                            {searchResults.results.length}
                          </p>
                        </CardContent>
                      </Card>
                    </div>
                  </div>

                  <Separator />

                  {/* Enhanced Queries */}
                  {useEnhancement && searchResults.enhanced_queries && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-base">Enhanced Queries</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <code className="text-sm bg-muted p-3 rounded block">
                          {searchResults.enhanced_queries.join(", ")}
                        </code>
                      </CardContent>
                    </Card>
                  )}

                  {/* Detailed Table */}
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                      <CardTitle className="text-base">Detailed Results Table</CardTitle>
                      <Button onClick={downloadCSV} size="sm" variant="outline">
                        <Download className="mr-2 h-4 w-4" />
                        Download CSV
                      </Button>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="border-b">
                            <tr>
                              <th className="text-left p-2">Rank</th>
                              <th className="text-left p-2">Filename</th>
                              <th className="text-left p-2">Similarity Score</th>
                              <th className="text-left p-2">Confidence</th>
                              <th className="text-left p-2">Matches</th>
                            </tr>
                          </thead>
                          <tbody>
                            {searchResults.results.map((result) => (
                              <tr key={result.rank} className="border-b">
                                <td className="p-2">{result.rank}</td>
                                <td className="p-2">{result.filename}</td>
                                <td className="p-2">{result.similarity_score.toFixed(3)}</td>
                                <td className="p-2">{result.confidence_percentage}</td>
                                <td className="p-2">{result.num_query_matches}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <Card className="p-12 text-center">
                  <Database className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">
                    Enter a query and click Search to begin visual retrieval
                  </p>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="status" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>System Status</CardTitle>
                </CardHeader>
                <CardContent>
                  {health.model ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium">Model:</p>
                          <code className="text-xs bg-muted p-1 rounded">
                            {health.model}
                          </code>
                        </div>
                        <div>
                          <p className="text-sm font-medium">Embedding Dimension:</p>
                          <code className="text-xs bg-muted p-1 rounded">
                            {health.embedding_dim}
                          </code>
                        </div>
                        <div>
                          <p className="text-sm font-medium">Vectors Indexed:</p>
                          <code className="text-xs bg-muted p-1 rounded">
                            {health.vectors_indexed?.toLocaleString()}
                          </code>
                        </div>
                        <div>
                          <p className="text-sm font-medium">Total Images:</p>
                          <code className="text-xs bg-muted p-1 rounded">
                            {health.total_images?.toLocaleString()}
                          </code>
                        </div>
                        <div>
                          <p className="text-sm font-medium">Index Type:</p>
                          <code className="text-xs bg-muted p-1 rounded">
                            {health.index_type}
                          </code>
                        </div>
                        <div>
                          <p className="text-sm font-medium">Device:</p>
                          <code className="text-xs bg-muted p-1 rounded">
                            {health.device}
                          </code>
                        </div>
                      </div>
                      <Separator />
                      <div className="flex items-center gap-2 text-green-600">
                        <Cpu className="h-5 w-5" />
                        <span className="font-semibold">System operational</span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-red-600">
                      <p className="font-semibold">Cannot connect to API</p>
                      <p className="text-sm text-muted-foreground mt-2">
                        Please check if the API server is running at {API_BASE}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
};

export default Index;

# BookVerse Recommendations Service - Operations Guide

**Production Operations, Monitoring, and Troubleshooting**

This guide provides comprehensive operational guidance for managing the BookVerse Recommendations Service in production environments, including monitoring, performance optimization, troubleshooting, and maintenance procedures.

---

## 📊 Monitoring & Observability

### Key Performance Indicators (KPIs)

#### **Service-Level Objectives (SLOs)**
| Metric | Target | Measurement Window |
|--------|--------|--------------------|
| Response Time (P95) | < 200ms | 5-minute rolling |
| Availability | > 99.9% | Monthly |
| Error Rate | < 0.1% | Hourly |
| Cache Hit Rate | > 85% | 15-minute rolling |
| Model Freshness | < 24 hours | Daily |

#### **Business Metrics**
| Metric | Target | Measurement Window |
|--------|--------|--------------------|
| Click-Through Rate | > 15% | Daily |
| Conversion Rate | > 2% | Weekly |
| Recommendation Coverage | > 95% | Daily |
| Model Accuracy (NDCG@10) | > 0.75 | Weekly |

### Monitoring Stack

#### **Application Metrics**
```python
# Prometheus metrics configuration
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
request_count = Counter(
    'recommendations_requests_total',
    'Total recommendation requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'recommendations_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# Model metrics
model_prediction_time = Histogram(
    'model_prediction_duration_seconds',
    'Model prediction time',
    ['model_type']
)

cache_hit_rate = Gauge(
    'cache_hit_rate_percent',
    'Cache hit rate percentage'
)

# Business metrics
recommendation_clicks = Counter(
    'recommendation_clicks_total',
    'Total recommendation clicks',
    ['user_segment', 'recommendation_type']
)
```

#### **Infrastructure Metrics**
```yaml
# Grafana dashboard configuration
dashboard:
  title: "BookVerse Recommendations Service"
  panels:
    - title: "Request Rate"
      type: "graph"
      targets:
        - expr: "rate(recommendations_requests_total[5m])"
          legend: "RPS"
    
    - title: "Response Time Distribution"
      type: "graph"
      targets:
        - expr: "histogram_quantile(0.95, recommendations_request_duration_seconds_bucket)"
          legend: "P95"
        - expr: "histogram_quantile(0.50, recommendations_request_duration_seconds_bucket)"
          legend: "P50"
    
    - title: "Error Rate"
      type: "singlestat"
      targets:
        - expr: "rate(recommendations_requests_total{status=~'4..|5..'}[5m]) / rate(recommendations_requests_total[5m])"
    
    - title: "Cache Performance"
      type: "graph"
      targets:
        - expr: "cache_hit_rate_percent"
          legend: "Hit Rate %"
```

### Alerting Rules

#### **Critical Alerts**
```yaml
# Prometheus alerting rules
groups:
  - name: recommendations.critical
    rules:
      - alert: HighErrorRate
        expr: rate(recommendations_requests_total{status=~'5..'}[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in recommendations service"
          description: "Error rate is {{ $value }} for the last 5 minutes"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, recommendations_request_duration_seconds_bucket) > 0.5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High response time in recommendations service"
          description: "P95 response time is {{ $value }}s"

      - alert: ServiceDown
        expr: up{job="recommendations-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Recommendations service is down"
          description: "Service has been down for more than 1 minute"
```

#### **Warning Alerts**
```yaml
  - name: recommendations.warning
    rules:
      - alert: LowCacheHitRate
        expr: cache_hit_rate_percent < 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}% for the last 10 minutes"

      - alert: ModelStaleness
        expr: time() - model_last_update_timestamp > 86400
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "ML model is stale"
          description: "Model hasn't been updated for more than 24 hours"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}% of limit"
```

### Health Checks

#### **Readiness Probe**
```python
@app.get("/health/ready")
async def readiness_check():
    """
    Comprehensive readiness check for load balancer routing.
    
    Verifies all critical dependencies are available:
    - Redis cache connectivity
    - Model availability
    - Upstream service connectivity
    """
    checks = {
        "redis": False,
        "models": False,
        "inventory_service": False
    }
    
    try:
        # Check Redis connectivity
        await redis_client.ping()
        checks["redis"] = True
        
        # Check model availability
        model_status = await model_registry.get_active_models()
        checks["models"] = len(model_status) > 0
        
        # Check upstream services
        inventory_response = await inventory_client.health_check()
        checks["inventory_service"] = inventory_response.status_code == 200
        
        # All checks must pass for readiness
        is_ready = all(checks.values())
        
        return {
            "status": "ready" if is_ready else "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.exception("Health check failed")
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e),
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

#### **Liveness Probe**
```python
@app.get("/health/live")
async def liveness_check():
    """
    Basic liveness check for Kubernetes restart decisions.
    
    Only checks that the application process is responsive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - app_start_time
    }
```

---

## 🚀 Performance Optimization

### Response Time Optimization

#### **Caching Strategies**
```python
class MultiLevelCache:
    def __init__(self):
        self.l1_cache = {}  # In-memory LRU cache
        self.l2_cache = redis_client  # Redis cache
        self.l3_cache = model_cache  # Precomputed recommendations
    
    async def get_recommendations(self, user_id: str, context: Dict) -> List[Recommendation]:
        cache_key = self.generate_cache_key(user_id, context)
        
        # L1: Check in-memory cache
        if cache_key in self.l1_cache:
            return self.l1_cache[cache_key]
        
        # L2: Check Redis cache
        cached_result = await self.l2_cache.get(cache_key)
        if cached_result:
            recommendations = self.deserialize(cached_result)
            self.l1_cache[cache_key] = recommendations  # Populate L1
            return recommendations
        
        # L3: Check precomputed cache
        precomputed = await self.l3_cache.get_precomputed(user_id)
        if precomputed and self.is_valid(precomputed, context):
            await self.l2_cache.setex(cache_key, 300, self.serialize(precomputed))
            self.l1_cache[cache_key] = precomputed
            return precomputed
        
        # Cache miss: Generate recommendations
        recommendations = await self.generate_recommendations(user_id, context)
        
        # Populate all cache levels
        await self.l2_cache.setex(cache_key, 300, self.serialize(recommendations))
        self.l1_cache[cache_key] = recommendations
        
        return recommendations
```

#### **Database Query Optimization**
```python
class OptimizedQueryManager:
    def __init__(self):
        self.connection_pool = ConnectionPool(
            max_connections=50,
            retry_on_timeout=True
        )
    
    async def batch_fetch_features(self, item_ids: List[str]) -> Dict[str, Dict]:
        """Batch fetch item features to minimize database round trips."""
        
        # Use batch queries with LIMIT to prevent memory issues
        batch_size = 100
        all_features = {}
        
        for i in range(0, len(item_ids), batch_size):
            batch_ids = item_ids[i:i + batch_size]
            
            # Single query for batch instead of N individual queries
            query = """
                SELECT item_id, title, genres, price, rating, features
                FROM items 
                WHERE item_id = ANY(%s)
            """
            
            async with self.connection_pool.acquire() as conn:
                results = await conn.fetch(query, batch_ids)
                
                for row in results:
                    all_features[row['item_id']] = {
                        'title': row['title'],
                        'genres': row['genres'],
                        'price': row['price'],
                        'rating': row['rating'],
                        'features': row['features']
                    }
        
        return all_features
```

### Model Inference Optimization

#### **Model Quantization**
```python
class QuantizedModelWrapper:
    def __init__(self, model_path: str, quantization_bits: int = 8):
        self.quantization_bits = quantization_bits
        self.model = self.load_and_quantize_model(model_path)
    
    def load_and_quantize_model(self, model_path: str):
        """Load model and apply quantization for faster inference."""
        
        # Load original model
        original_model = tf.keras.models.load_model(model_path)
        
        # Apply quantization
        converter = tf.lite.TFLiteConverter.from_keras_model(original_model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Quantize weights to reduce model size and improve speed
        if self.quantization_bits == 8:
            converter.target_spec.supported_types = [tf.int8]
        elif self.quantization_bits == 16:
            converter.target_spec.supported_types = [tf.float16]
        
        quantized_model = converter.convert()
        
        # Load quantized model for inference
        interpreter = tf.lite.Interpreter(model_content=quantized_model)
        interpreter.allocate_tensors()
        
        return interpreter
    
    def predict(self, input_data: np.ndarray) -> np.ndarray:
        """Fast inference using quantized model."""
        
        input_details = self.model.get_input_details()
        output_details = self.model.get_output_details()
        
        # Set input data
        self.model.set_tensor(input_details[0]['index'], input_data)
        
        # Run inference
        self.model.invoke()
        
        # Get output
        output_data = self.model.get_tensor(output_details[0]['index'])
        
        return output_data
```

#### **Batch Processing**
```python
class BatchInferenceProcessor:
    def __init__(self, batch_size: int = 64, max_wait_time: float = 0.1):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests = []
        self.request_futures = {}
    
    async def predict_batch(self, user_features: np.ndarray, item_features: np.ndarray) -> np.ndarray:
        """Process prediction requests in batches for efficiency."""
        
        request_id = str(uuid4())
        future = asyncio.Future()
        
        self.pending_requests.append({
            'request_id': request_id,
            'user_features': user_features,
            'item_features': item_features,
            'timestamp': time.time()
        })
        
        self.request_futures[request_id] = future
        
        # Process batch if conditions are met
        await self.maybe_process_batch()
        
        return await future
    
    async def maybe_process_batch(self):
        """Process batch if size or time thresholds are met."""
        
        if not self.pending_requests:
            return
        
        should_process = (
            len(self.pending_requests) >= self.batch_size or
            time.time() - self.pending_requests[0]['timestamp'] > self.max_wait_time
        )
        
        if should_process:
            await self.process_current_batch()
    
    async def process_current_batch(self):
        """Execute batch inference and return results."""
        
        if not self.pending_requests:
            return
        
        # Prepare batch data
        batch_user_features = []
        batch_item_features = []
        request_ids = []
        
        for request in self.pending_requests:
            batch_user_features.append(request['user_features'])
            batch_item_features.append(request['item_features'])
            request_ids.append(request['request_id'])
        
        # Run batch inference
        try:
            user_batch = np.vstack(batch_user_features)
            item_batch = np.vstack(batch_item_features)
            
            predictions = await self.model.predict_batch(user_batch, item_batch)
            
            # Return results to individual futures
            for i, request_id in enumerate(request_ids):
                if request_id in self.request_futures:
                    self.request_futures[request_id].set_result(predictions[i])
                    del self.request_futures[request_id]
        
        except Exception as e:
            # Handle batch failure
            for request_id in request_ids:
                if request_id in self.request_futures:
                    self.request_futures[request_id].set_exception(e)
                    del self.request_futures[request_id]
        
        finally:
            self.pending_requests.clear()
```

---

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### **High Response Time**

**Symptoms:**
- P95 response time > 200ms
- Timeout errors in client applications
- User complaints about slow recommendations

**Diagnostic Steps:**
```bash
# Check current response times
curl -w "@curl-format.txt" -s "http://recommendations-service/api/v1/users/123/recommendations"

# Check cache hit rates
kubectl exec -n bookverse recommendations-api-xxx -- redis-cli info stats | grep keyspace_hits

# Review resource utilization
kubectl top pods -n bookverse | grep recommendations

# Check for database slow queries
kubectl logs -n bookverse recommendations-api-xxx | grep "slow_query"
```

**Solutions:**
1. **Cache Optimization:**
   ```python
   # Increase cache TTL for stable recommendations
   CACHE_TTL_SECONDS = 900  # 15 minutes
   
   # Implement cache warming
   async def warm_cache_for_active_users():
       active_users = await get_active_users(hours=24)
       for user_id in active_users:
           await generate_and_cache_recommendations(user_id)
   ```

2. **Resource Scaling:**
   ```bash
   # Increase pod resources
   kubectl patch deployment recommendations-api -n bookverse -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","resources":{"requests":{"cpu":"1000m","memory":"2Gi"}}}]}}}}'
   
   # Scale horizontally
   kubectl scale deployment recommendations-api -n bookverse --replicas=5
   ```

#### **Low Cache Hit Rate**

**Symptoms:**
- Cache hit rate < 80%
- High database load
- Increased model inference calls

**Diagnostic Steps:**
```bash
# Analyze cache patterns
redis-cli --scan --pattern "recommendations:*" | head -20
redis-cli info memory

# Check cache eviction
redis-cli info stats | grep evicted_keys

# Review cache key distribution
redis-cli --eval "return #redis.call('keys', '*')" 0
```

**Solutions:**
1. **Cache Key Optimization:**
   ```python
   class SmartCacheKeyGenerator:
       def generate_key(self, user_id: str, context: Dict) -> str:
           # Use less granular context for higher hit rates
           simplified_context = {
               'time_of_day': self.get_time_bucket(context.get('timestamp')),
               'device_type': context.get('device_type', 'web'),
               'user_segment': self.get_user_segment(user_id)
           }
           
           context_hash = hashlib.md5(
               json.dumps(simplified_context, sort_keys=True).encode()
           ).hexdigest()[:8]
           
           return f"recommendations:{user_id}:{context_hash}"
       
       def get_time_bucket(self, timestamp):
           """Bucket time into 4-hour windows for cache efficiency."""
           hour = timestamp.hour
           return hour // 4  # 0-5 buckets per day
   ```

2. **Cache Precomputation:**
   ```python
   async def precompute_popular_recommendations():
       """Precompute recommendations for common scenarios."""
       
       # Popular user segments
       segments = ['new_user', 'active_reader', 'casual_browser']
       
       for segment in segments:
           recommendations = await generate_segment_recommendations(segment)
           await cache.setex(
               f"recommendations:segment:{segment}",
               3600,  # 1 hour TTL
               recommendations
           )
   ```

#### **Model Performance Degradation**

**Symptoms:**
- Declining click-through rates
- Poor recommendation relevance
- User feedback indicating poor quality

**Diagnostic Steps:**
```bash
# Check model metrics
curl http://recommendations-service/metrics | grep model_accuracy

# Review model staleness
kubectl logs -n bookverse recommendations-worker-xxx | grep "model_update"

# Analyze recommendation quality
python scripts/analyze_recommendation_quality.py --days=7
```

**Solutions:**
1. **Model Retraining:**
   ```python
   class AutoRetrainingPipeline:
       def __init__(self):
           self.performance_threshold = 0.75  # NDCG@10
           self.staleness_threshold = 86400   # 24 hours
       
       async def check_and_retrain(self):
           current_performance = await self.evaluate_current_model()
           model_age = await self.get_model_age()
           
           should_retrain = (
               current_performance < self.performance_threshold or
               model_age > self.staleness_threshold
           )
           
           if should_retrain:
               logger.info("Triggering model retraining")
               await self.trigger_retraining_pipeline()
   ```

2. **A/B Testing Recovery:**
   ```python
   # Implement fallback to previous model version
   async def fallback_to_previous_model():
       previous_version = await model_registry.get_previous_version()
       await model_registry.promote_model(previous_version, 'production')
       
       # Gradually ramp traffic to new model
       await traffic_splitter.set_split({
           'current_model': 80,
           'previous_model': 20
       })
   ```

### Emergency Procedures

#### **Service Degradation Response**

**Immediate Actions (0-5 minutes):**
```bash
# 1. Check service status
kubectl get pods -n bookverse | grep recommendations
kubectl describe pod recommendations-api-xxx -n bookverse

# 2. Check resource utilization
kubectl top pods -n bookverse recommendations-api-xxx
kubectl top nodes

# 3. Scale up immediately if needed
kubectl scale deployment recommendations-api -n bookverse --replicas=10

# 4. Enable fallback mode
curl -X POST http://recommendations-service/admin/enable-fallback-mode
```

**Short-term Actions (5-30 minutes):**
```bash
# 1. Investigate root cause
kubectl logs -n bookverse recommendations-api-xxx --tail=1000 | grep ERROR

# 2. Check dependencies
curl http://inventory-service/health
curl http://redis-service:6379/ping

# 3. Review recent deployments
kubectl rollout history deployment/recommendations-api -n bookverse

# 4. Consider rollback if needed
kubectl rollout undo deployment/recommendations-api -n bookverse
```

#### **Data Loss Recovery**

**Cache Recovery:**
```python
async def recover_cache_from_backup():
    """Recover cache from persistent backup."""
    
    # Load from last known good state
    backup_file = await get_latest_cache_backup()
    
    with open(backup_file, 'rb') as f:
        cache_data = pickle.load(f)
    
    # Restore to Redis
    pipe = redis_client.pipeline()
    for key, value in cache_data.items():
        pipe.setex(key, 3600, value)  # 1 hour TTL
    
    await pipe.execute()
    logger.info(f"Restored {len(cache_data)} cache entries from backup")
```

**Model Recovery:**
```python
async def recover_model_from_registry():
    """Recover from model registry backup."""
    
    # Get last stable model version
    stable_version = await model_registry.get_last_stable_version()
    
    # Download and deploy
    model_artifacts = await model_registry.download_model(stable_version)
    await model_deployer.deploy_model(model_artifacts)
    
    logger.info(f"Recovered model version {stable_version}")
```

---

## 🔄 Maintenance Procedures

### Routine Maintenance

#### **Daily Tasks**
```bash
#!/bin/bash
# daily_maintenance.sh

# Check service health
kubectl get pods -n bookverse | grep recommendations

# Review error logs
kubectl logs -n bookverse recommendations-api-xxx --since=24h | grep ERROR | wc -l

# Check cache memory usage
kubectl exec -n bookverse recommendations-api-xxx -- redis-cli info memory

# Verify model freshness
curl -s http://recommendations-service/admin/model-status | jq '.last_update'

# Clean up old cache keys
kubectl exec -n bookverse recommendations-api-xxx -- redis-cli eval "
local keys = redis.call('keys', 'recommendations:*')
local expired = 0
for i=1,#keys do
    local ttl = redis.call('ttl', keys[i])
    if ttl == -1 then
        redis.call('expire', keys[i], 3600)
        expired = expired + 1
    end
end
return expired
" 0
```

#### **Weekly Tasks**
```bash
#!/bin/bash
# weekly_maintenance.sh

# Model performance evaluation
python scripts/evaluate_model_performance.py --period=week

# Cache optimization analysis
python scripts/analyze_cache_patterns.py --days=7

# Resource usage review
kubectl top pods -n bookverse --sort-by=memory | grep recommendations

# Update model training data
python scripts/prepare_training_data.py --incremental

# Security scan
trivy image bookverse/recommendations:latest
```

#### **Monthly Tasks**
```bash
#!/bin/bash
# monthly_maintenance.sh

# Full model retraining
python scripts/full_model_retrain.py

# Performance baseline update
python scripts/update_performance_baselines.py

# Capacity planning review
python scripts/generate_capacity_report.py --period=month

# Dependency updates
pip-audit
safety check

# Configuration backup
kubectl get configmap recommendations-config -n bookverse -o yaml > backup/config-$(date +%Y%m%d).yaml
```

### Deployment Procedures

#### **Blue-Green Deployment**
```bash
#!/bin/bash
# blue_green_deploy.sh

NEW_VERSION=$1
CURRENT_VERSION=$(kubectl get deployment recommendations-api -n bookverse -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)

echo "Deploying version $NEW_VERSION (current: $CURRENT_VERSION)"

# Deploy green environment
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommendations-api-green
  namespace: bookverse
spec:
  replicas: 3
  selector:
    matchLabels:
      app: recommendations-api
      version: green
  template:
    metadata:
      labels:
        app: recommendations-api
        version: green
    spec:
      containers:
      - name: api
        image: bookverse/recommendations:$NEW_VERSION
        ports:
        - containerPort: 8001
EOF

# Wait for green deployment to be ready
kubectl wait --for=condition=available --timeout=300s deployment/recommendations-api-green -n bookverse

# Health check green environment
GREEN_POD=$(kubectl get pods -n bookverse -l version=green -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward -n bookverse $GREEN_POD 8080:8001 &
PF_PID=$!

sleep 5
HEALTH_STATUS=$(curl -s http://localhost:8080/health/ready | jq -r '.status')

kill $PF_PID

if [ "$HEALTH_STATUS" = "ready" ]; then
    echo "Green environment is healthy, switching traffic"
    
    # Update service to point to green
    kubectl patch service recommendations-api -n bookverse -p '{"spec":{"selector":{"version":"green"}}}'
    
    # Wait and verify
    sleep 30
    
    # If successful, clean up blue
    kubectl delete deployment recommendations-api-blue -n bookverse 2>/dev/null || true
    kubectl patch deployment recommendations-api -n bookverse -p '{"metadata":{"name":"recommendations-api-blue"}}'
    kubectl patch deployment recommendations-api-green -n bookverse -p '{"metadata":{"name":"recommendations-api"}}'
    
    echo "Deployment successful"
else
    echo "Green environment health check failed, rolling back"
    kubectl delete deployment recommendations-api-green -n bookverse
    exit 1
fi
```

#### **Canary Deployment**
```bash
#!/bin/bash
# canary_deploy.sh

NEW_VERSION=$1
CANARY_PERCENTAGE=${2:-10}

echo "Starting canary deployment for version $NEW_VERSION ($CANARY_PERCENTAGE% traffic)"

# Deploy canary version
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recommendations-api-canary
  namespace: bookverse
spec:
  replicas: 1
  selector:
    matchLabels:
      app: recommendations-api
      version: canary
  template:
    metadata:
      labels:
        app: recommendations-api
        version: canary
    spec:
      containers:
      - name: api
        image: bookverse/recommendations:$NEW_VERSION
EOF

# Configure traffic splitting
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: recommendations-api
  namespace: bookverse
spec:
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: recommendations-api
        subset: canary
      weight: 100
  - route:
    - destination:
        host: recommendations-api
        subset: stable
      weight: $((100 - CANARY_PERCENTAGE))
    - destination:
        host: recommendations-api
        subset: canary
      weight: $CANARY_PERCENTAGE
EOF

echo "Canary deployment active. Monitor metrics and run promote_canary.sh when ready."
```

---

## 📈 Capacity Planning

### Resource Scaling Guidelines

#### **CPU Scaling**
```python
class CPUScalingCalculator:
    def __init__(self):
        self.baseline_rps = 1000
        self.baseline_cpu_cores = 2
        self.cpu_efficiency_factor = 0.8
    
    def calculate_required_cpu(self, target_rps: int) -> float:
        """Calculate CPU cores needed for target RPS."""
        
        scaling_factor = target_rps / self.baseline_rps
        raw_cpu_needed = self.baseline_cpu_cores * scaling_factor
        
        # Add overhead for inefficiency
        cpu_with_overhead = raw_cpu_needed / self.cpu_efficiency_factor
        
        # Round up to nearest 0.5 core
        return math.ceil(cpu_with_overhead * 2) / 2
    
    def generate_scaling_plan(self, growth_projections: List[int]) -> Dict:
        """Generate scaling plan for projected growth."""
        
        plan = {}
        for month, projected_rps in enumerate(growth_projections, 1):
            required_cpu = self.calculate_required_cpu(projected_rps)
            
            plan[f"month_{month}"] = {
                "projected_rps": projected_rps,
                "required_cpu_cores": required_cpu,
                "recommended_instances": math.ceil(required_cpu / 4),  # 4 cores per instance
                "estimated_cost": self.estimate_cost(required_cpu)
            }
        
        return plan
```

#### **Memory Scaling**
```python
class MemoryScalingCalculator:
    def __init__(self):
        self.cache_memory_per_user = 1024  # 1KB per active user
        self.model_memory_base = 500 * 1024 * 1024  # 500MB base model
        self.application_overhead = 512 * 1024 * 1024  # 512MB overhead
    
    def calculate_required_memory(self, active_users: int, model_count: int = 3) -> int:
        """Calculate memory needed for given user base."""
        
        cache_memory = active_users * self.cache_memory_per_user
        model_memory = model_count * self.model_memory_base
        total_memory = cache_memory + model_memory + self.application_overhead
        
        # Add 20% buffer
        return int(total_memory * 1.2)
    
    def recommend_pod_memory(self, required_memory: int) -> str:
        """Recommend Kubernetes memory request/limit."""
        
        # Convert to Gi and round up
        memory_gi = math.ceil(required_memory / (1024**3))
        
        return f"{memory_gi}Gi"
```

### Auto-scaling Configuration

#### **Horizontal Pod Autoscaler**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: recommendations-api-hpa
  namespace: bookverse
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: recommendations-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "500"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 120
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### **Vertical Pod Autoscaler**
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: recommendations-api-vpa
  namespace: bookverse
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: recommendations-api
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: api
      maxAllowed:
        cpu: 4
        memory: 8Gi
      minAllowed:
        cpu: 100m
        memory: 256Mi
      controlledResources: ["cpu", "memory"]
```

---

## 🔗 Related Documentation

- **[Architecture Guide](ARCHITECTURE.md)**: System architecture and scaling strategies
- **[Machine Learning Guide](MACHINE_LEARNING.md)**: ML model operations and evaluation
- **[Algorithm Guide](ALGORITHM_GUIDE.md)**: Recommendation algorithms and configuration
- **[Development Guide](DEVELOPMENT_GUIDE.md)**: Local development and testing
- **[API Reference](../api/README.md)**: Complete API documentation

---

**Authors**: BookVerse Platform Team  
**Version**: 1.0.0  
**Last Updated**: 2024-01-01

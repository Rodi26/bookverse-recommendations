# Deployment

- Deployed as part of the single platform Helm chart release
- Recommendations API/Service and Worker run as separate Deployments
- Toggle worker via values: `recommendations.worker.enabled`
- Mount config/resources via ConfigMaps included in the chart
- Web UI is the only interaction surface for the demo

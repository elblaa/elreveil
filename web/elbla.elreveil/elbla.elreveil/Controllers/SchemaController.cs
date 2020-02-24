using System.Linq;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using System.IO;
using Newtonsoft.Json;
using Microsoft.Extensions.Configuration;

namespace elbla.elreveil.Controllers
{
    [Produces("application/json")]
    public class SchemaController : Controller
    {
        private readonly ILogger<SchemaController> _logger;
        private readonly IConfiguration _configuration;

        public SchemaController(ILogger<SchemaController> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
        }

        public IActionResult Index()
        {
            return View();
        }

        public IActionResult Schema(string schemaFileAsked)
        {
            var folder = _configuration.GetValue<string>("schemaFolder");
            var files = Directory.GetFiles(folder);
            var schemaFile = files.FirstOrDefault(f => Path.GetFileName(f) == schemaFileAsked + ".json");
            if (schemaFile == null)
            {
                _logger.LogError($"Unauthorized file {schemaFileAsked}");
                return new UnauthorizedResult();
            }

            var schema = System.IO.File.ReadAllText(schemaFile);
            var jsonSerialized = JsonConvert.DeserializeObject(schema);

            return new OkObjectResult(jsonSerialized);
        }
    }
}

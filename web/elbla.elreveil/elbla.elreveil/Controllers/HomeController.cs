using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

namespace elbla.elreveil.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;
        private readonly IConfiguration _configuration;

        public HomeController(ILogger<HomeController> logger, IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
        }

        public IActionResult Index()
        {
            return View();
        }

        [Produces("application/json")]
        public IActionResult Configuration()
        {
            var configurationSerialized = System.IO.File.ReadAllText(_configuration.GetValue<string>("configurationPath"));
            var jsonSerialized = JsonConvert.DeserializeObject(configurationSerialized);
            return new OkObjectResult(jsonSerialized);
        }

        [HttpPost]
        public IActionResult Save(string newValue)
        {
            var fileSaved = _configuration.GetValue<string>("configurationPath");
            var backupPath = _configuration.GetValue<string>("backupConfigurationPath");
            if (!string.IsNullOrEmpty(backupPath))
            {
                System.IO.File.Copy(fileSaved, backupPath);
            }

            System.IO.File.WriteAllText(fileSaved, newValue);
            return new OkResult();
        }
    }
}

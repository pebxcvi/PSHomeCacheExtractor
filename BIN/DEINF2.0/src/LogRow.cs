public class LogRow
{
    public string UriHash { get; set; }              // INF filename
    public string UriPath { get; set; }              // Extracted from INF
    public string WasEncrypted { get; set; }         // "Yes"/"No"
    public string Date { get; set; }                 // Extracted from INF
    public string EncryptedSha1 { get; set; }        // SHA1 of original INF
    public string DecryptedSha1 { get; set; }        // SHA1 of decrypted INF
}
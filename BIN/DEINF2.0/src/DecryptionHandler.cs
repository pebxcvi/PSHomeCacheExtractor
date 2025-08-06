using System;
using System.IO;

public static class DecryptionHandler
{
    public static void DecryptOrCopy(string inFile, string output, bool outputIsFile)
    {
        try
        {
            byte[] inputBytes = File.ReadAllBytes(inFile);

            string outFile = outputIsFile ? output : Path.Combine(output, Path.GetFileName(inFile));

            if (inputBytes.Length >= 4 &&
                inputBytes[0] == 0x00 && inputBytes[1] == 0x00 &&
                inputBytes[2] == 0x00 && inputBytes[3] == 0x01)
            {
                inputBytes = ToolsImplementation.RemovePaddingPrefix(inputBytes);
                byte[] decrypted = LIBSECURE.Crypt_Decrypt(inputBytes, ToolsImplementation.MetaDataV1IVA, 8);
                File.WriteAllBytes(outFile, decrypted);
            }
            else if (inputBytes.Length >= 4 &&
                     inputBytes[0] == 0xBE && inputBytes[1] == 0xE5 &&
                     inputBytes[2] == 0xBE && inputBytes[3] == 0xE5)
            {
                byte[] decrypted = LIBSECURE.Crypt_Decrypt(inputBytes, ToolsImplementation.MetaDataV1IVA, 8);
                File.WriteAllBytes(outFile, decrypted);
            }
            else
            {
                File.Copy(inFile, outFile, true);
            }
        }
        catch (Exception ex)
        {
            //Console.WriteLine($"ERROR: {inFile} -- {ex.Message}");
        }
    }
}
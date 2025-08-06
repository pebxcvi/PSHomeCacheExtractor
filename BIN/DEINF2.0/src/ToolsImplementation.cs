using System;
using Org.BouncyCastle.Crypto;
using Org.BouncyCastle.Crypto.Parameters;
using Org.BouncyCastle.Security;

public static class ToolsImplementation
{
    public static readonly byte[] MetaDataV1Key = new byte[32]
    {
        0x8B, 0x41, 0xA7, 0xDE, 0x47, 0xA0, 0xD4, 0x45,
        0xE2, 0xA5, 0x90, 0x34, 0x3C, 0xD9, 0xA8, 0xB5,
        0x69, 0x5E, 0xFA, 0xD9, 0x97, 0x32, 0xEC, 0x56,
        0x0B, 0x31, 0xE8, 0x5A, 0xD1, 0x85, 0x7C, 0x89
    };

    public static readonly byte[] MetaDataV1IV = new byte[8] { 0x2a, 0xa7, 0xcb, 0x49, 0x9f, 0xa1, 0xbd, 0x81 };

    private static byte[] InitiateMetaDataV1IVA()
    {
        const ushort metaSize = 528;
        byte[] nulledBytes = new byte[metaSize];

        IBufferedCipher cipher = CipherUtilities.GetCipher("Blowfish/CTR/NOPADDING");
        cipher.Init(false, new ParametersWithIV(new KeyParameter(MetaDataV1Key), MetaDataV1IV));
        byte[] ciphertextBytes = new byte[cipher.GetOutputSize(metaSize)];
        int ciphertextLength = cipher.ProcessBytes(nulledBytes, 0, metaSize, ciphertextBytes, 0);
        cipher.DoFinal(ciphertextBytes, ciphertextLength);
        cipher = null;

        return ciphertextBytes;
    }

    public static readonly byte[] MetaDataV1IVA = InitiateMetaDataV1IVA();

    public static byte[] ApplyLittleEndianPaddingPrefix(byte[] filebytes)
    {
        return ByteUtils.CombineByteArray(new byte[] { 0x00, 0x00, 0x00, 0x01 }, filebytes);
    }

    public static byte[] RemovePaddingPrefix(byte[] fileBytes)
    {
        if (fileBytes.Length > 4 && ((fileBytes[0] == 0x00 && fileBytes[1] == 0x00 && fileBytes[2] == 0x00 && fileBytes[3] == 0x01)
            || (fileBytes[0] == 0x01 && fileBytes[1] == 0x00 && fileBytes[2] == 0x00 && fileBytes[3] == 0x00)))
        {
            byte[] destinationArray = new byte[fileBytes.Length - 4];
            Array.Copy(fileBytes, 4, destinationArray, 0, destinationArray.Length);
            return destinationArray;
        }
        return fileBytes;
    }
}
